"""Input/output operations for reading and writing data."""

import hashlib
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import pandas as pd

from phoenix_pipeline.config import settings

logger = logging.getLogger(__name__)


# =============================================================================
# Standalone I/O Functions
# =============================================================================


def read_state(path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Read pipeline state from JSON file.

    Args:
        path: Path to state file (defaults to settings.state_path)

    Returns:
        State dictionary with at least 'last_processed_block' (default 0)

    Example:
        >>> state = read_state()
        >>> print(state['last_processed_block'])
        18000000
    """
    state_path = path or settings.state_path

    if not state_path.exists():
        logger.info(f"No state file found at {state_path}, returning default state")
        return {"last_processed_block": 0}

    try:
        with open(state_path, "r") as f:
            state = json.load(f)

        # Ensure required keys exist
        if "last_processed_block" not in state:
            state["last_processed_block"] = 0

        logger.info(f"Loaded state from {state_path}: last_processed_block={state['last_processed_block']}")
        return state

    except (json.JSONDecodeError, IOError) as e:
        logger.error(f"Error reading state file {state_path}: {e}")
        return {"last_processed_block": 0}


def write_state(path: Optional[Path] = None, block: Optional[int] = None, **kwargs: Any) -> None:
    """
    Write pipeline state to JSON file.

    Args:
        path: Path to state file (defaults to settings.state_path)
        block: Block number to save as 'last_processed_block'
        **kwargs: Additional state fields to save

    Example:
        >>> write_state(block=18000000, last_updated="2025-01-01T00:00:00")
    """
    state_path = path or settings.state_path

    # Ensure parent directory exists
    state_path.parent.mkdir(parents=True, exist_ok=True)

    # Build state dictionary
    state: Dict[str, Any] = {}

    # Load existing state if it exists
    if state_path.exists():
        try:
            with open(state_path, "r") as f:
                state = json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"Could not load existing state, starting fresh: {e}")
            state = {}

    # Update with new values
    if block is not None:
        state["last_processed_block"] = block
        state["last_updated"] = pd.Timestamp.now().isoformat()

    # Add any additional kwargs
    state.update(kwargs)

    # Write to file
    try:
        with open(state_path, "w") as f:
            json.dump(state, f, indent=2)
        logger.info(f"Wrote state to {state_path}: last_processed_block={state.get('last_processed_block', 'N/A')}")
    except IOError as e:
        logger.error(f"Error writing state file {state_path}: {e}")
        raise


def write_json(path: Path, data: Union[Dict[str, Any], List[Any]]) -> None:
    """
    Write dictionary or list to JSON file.

    Args:
        path: Output file path
        data: Dictionary or list to write

    Example:
        >>> write_json(Path("output.json"), {"key": "value"})
        >>> write_json(Path("list.json"), [{"id": 1}, {"id": 2}])
    """
    # Ensure parent directory exists
    path.parent.mkdir(parents=True, exist_ok=True)

    try:
        with open(path, "w") as f:
            json.dump(data, f, indent=2)

        item_count = len(data) if isinstance(data, (list, dict)) else 0
        logger.info(f"Wrote {item_count} items to {path}")

    except (IOError, TypeError) as e:
        logger.error(f"Error writing JSON to {path}: {e}")
        raise


def write_csv(path: Path, dataframe: pd.DataFrame) -> None:
    """
    Write DataFrame to CSV file.

    Args:
        path: Output file path
        dataframe: DataFrame to write

    Example:
        >>> df = pd.DataFrame({"a": [1, 2], "b": [3, 4]})
        >>> write_csv(Path("output.csv"), df)
    """
    # Ensure parent directory exists
    path.parent.mkdir(parents=True, exist_ok=True)

    try:
        dataframe.to_csv(path, index=False)
        logger.info(f"Wrote {len(dataframe)} rows to {path}")
    except IOError as e:
        logger.error(f"Error writing CSV to {path}: {e}")
        raise


def filter_swaps_by_block(
    swaps: Union[pd.DataFrame, List[Dict[str, Any]]],
    last_processed_block: int,
) -> Union[pd.DataFrame, List[Dict[str, Any]]]:
    """
    Filter swaps to only include those after the last processed block.

    This implements idempotency by ensuring we don't reprocess old swaps.

    Args:
        swaps: DataFrame or list of swap dictionaries
        last_processed_block: Block number to filter against

    Returns:
        Filtered swaps (same type as input)

    Example:
        >>> swaps = [{"blockNumber": 100}, {"blockNumber": 200}]
        >>> filtered = filter_swaps_by_block(swaps, 150)
        >>> len(filtered)
        1
    """
    if isinstance(swaps, pd.DataFrame):
        if "blockNumber" not in swaps.columns:
            logger.warning("blockNumber column not found, returning all swaps")
            return swaps

        initial_count = len(swaps)
        filtered = swaps[swaps["blockNumber"] > last_processed_block].copy()
        removed_count = initial_count - len(filtered)

        if removed_count > 0:
            logger.info(
                f"Filtered {removed_count} swaps at or before block {last_processed_block} "
                f"({len(filtered)} remaining)"
            )
        else:
            logger.debug(f"All {len(filtered)} swaps are after block {last_processed_block}")

        return filtered

    elif isinstance(swaps, list):
        initial_count = len(swaps)
        filtered = [s for s in swaps if s.get("blockNumber", 0) > last_processed_block]
        removed_count = initial_count - len(filtered)

        if removed_count > 0:
            logger.info(
                f"Filtered {removed_count} swaps at or before block {last_processed_block} "
                f"({len(filtered)} remaining)"
            )
        else:
            logger.debug(f"All {len(filtered)} swaps are after block {last_processed_block}")

        return filtered

    else:
        raise TypeError(f"Unsupported swaps type: {type(swaps)}")


def compute_data_hash(data: Union[pd.DataFrame, List[Any], Dict[str, Any]]) -> str:
    """
    Compute SHA256 hash of data for idempotency checks.

    Args:
        data: DataFrame, list, or dictionary to hash

    Returns:
        Hex string of SHA256 hash

    Example:
        >>> df = pd.DataFrame({"a": [1, 2]})
        >>> hash1 = compute_data_hash(df)
        >>> hash2 = compute_data_hash(df)
        >>> hash1 == hash2
        True
    """
    if isinstance(data, pd.DataFrame):
        # Use DataFrame's string representation for hashing
        # Convert to JSON string for consistency
        json_str = data.to_json(orient="records", date_format="iso")
    elif isinstance(data, (list, dict)):
        # Convert to JSON string
        json_str = json.dumps(data, sort_keys=True, default=str)
    else:
        raise TypeError(f"Unsupported data type for hashing: {type(data)}")

    # Compute SHA256 hash
    hash_obj = hashlib.sha256(json_str.encode("utf-8"))
    return hash_obj.hexdigest()


def should_skip_write(path: Path, data: Union[pd.DataFrame, List[Any], Dict[str, Any]]) -> bool:
    """
    Check if data should be skipped (already written with same hash).

    Args:
        path: File path to check
        data: Data to compare

    Returns:
        True if file exists with same hash, False otherwise

    Note:
        Hash is stored in {path}.hash file
    """
    hash_path = Path(str(path) + ".hash")

    if not path.exists() or not hash_path.exists():
        return False

    try:
        # Read existing hash
        with open(hash_path, "r") as f:
            existing_hash = f.read().strip()

        # Compute new hash
        new_hash = compute_data_hash(data)

        if existing_hash == new_hash:
            logger.info(f"Data unchanged, skipping write to {path}")
            return True
        else:
            logger.debug(f"Data changed, will write to {path}")
            return False

    except (IOError, json.JSONDecodeError) as e:
        logger.warning(f"Could not check hash for {path}: {e}")
        return False


def write_with_hash(
    path: Path,
    data: Union[pd.DataFrame, List[Any], Dict[str, Any]],
    format: str = "csv",
) -> bool:
    """
    Write data to file with hash tracking for idempotency.

    Args:
        path: Output file path
        data: Data to write
        format: Output format (csv, json)

    Returns:
        True if written, False if skipped

    Example:
        >>> df = pd.DataFrame({"a": [1, 2]})
        >>> write_with_hash(Path("output.csv"), df)  # Returns True (written)
        >>> write_with_hash(Path("output.csv"), df)  # Returns False (skipped, unchanged)
    """
    if should_skip_write(path, data):
        return False

    # Write data
    if format == "csv":
        if isinstance(data, pd.DataFrame):
            write_csv(path, data)
        else:
            raise TypeError("CSV format requires DataFrame")
    elif format == "json":
        if isinstance(data, pd.DataFrame):
            data.to_json(path, orient="records", indent=2, date_format="iso")
            logger.info(f"Wrote {len(data)} rows to {path}")
        else:
            write_json(path, data)
    else:
        raise ValueError(f"Unsupported format: {format}")

    # Write hash
    hash_path = Path(str(path) + ".hash")
    data_hash = compute_data_hash(data)
    try:
        with open(hash_path, "w") as f:
            f.write(data_hash)
        logger.debug(f"Wrote hash to {hash_path}")
    except IOError as e:
        logger.warning(f"Could not write hash file: {e}")

    return True


# =============================================================================
# Class-based API (Existing)
# =============================================================================


class StateManager:
    """Manage pipeline state for tracking progress."""

    def __init__(self, state_file: Optional[Path] = None) -> None:
        """
        Initialize state manager.

        Args:
            state_file: Path to state file (defaults to settings)
        """
        self.state_file = state_file or settings.state_path
        self.state_file.parent.mkdir(parents=True, exist_ok=True)

    def load_state(self) -> Dict[str, Any]:
        """
        Load state from file.

        Returns:
            State dictionary with last processed block and other metadata
        """
        if not self.state_file.exists():
            logger.info("No existing state file found, starting fresh")
            return {"last_processed_block": 0}

        try:
            with open(self.state_file, "r") as f:
                state = json.load(f)
            logger.info(f"Loaded state: last processed block = {state.get('last_processed_block', 0)}")
            return state
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"Error loading state file: {e}")
            return {"last_processed_block": 0}

    def save_state(self, state: Dict[str, Any]) -> None:
        """
        Save state to file.

        Args:
            state: State dictionary to save
        """
        try:
            with open(self.state_file, "w") as f:
                json.dump(state, f, indent=2)
            logger.info(f"Saved state: last processed block = {state.get('last_processed_block', 0)}")
        except IOError as e:
            logger.error(f"Error saving state file: {e}")
            raise

    def update_last_processed_block(self, block_number: int) -> None:
        """
        Update the last processed block number.

        Args:
            block_number: Block number to save
        """
        state = self.load_state()
        state["last_processed_block"] = block_number
        state["last_updated"] = pd.Timestamp.now().isoformat()
        self.save_state(state)

    def get_last_processed_block(self) -> int:
        """
        Get the last processed block number.

        Returns:
            Last processed block number
        """
        state = self.load_state()
        return state.get("last_processed_block", 0)


class DataWriter:
    """Write data to various output formats."""

    def __init__(self, output_dir: Optional[Path] = None) -> None:
        """
        Initialize data writer.

        Args:
            output_dir: Output directory path (defaults to settings)
        """
        self.output_dir = output_dir or settings.output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def write_csv(self, df: pd.DataFrame, filename: str) -> Path:
        """
        Write DataFrame to CSV file.

        Args:
            df: DataFrame to write
            filename: Output filename (without extension)

        Returns:
            Path to written file
        """
        output_path = self.output_dir / f"{filename}.csv"
        df.to_csv(output_path, index=False)
        logger.info(f"Wrote {len(df)} rows to {output_path}")
        return output_path

    def write_json(self, df: pd.DataFrame, filename: str) -> Path:
        """
        Write DataFrame to JSON file.

        Args:
            df: DataFrame to write
            filename: Output filename (without extension)

        Returns:
            Path to written file
        """
        output_path = self.output_dir / f"{filename}.json"
        df.to_json(output_path, orient="records", indent=2, date_format="iso")
        logger.info(f"Wrote {len(df)} rows to {output_path}")
        return output_path

    def write_parquet(self, df: pd.DataFrame, filename: str) -> Path:
        """
        Write DataFrame to Parquet file.

        Args:
            df: DataFrame to write
            filename: Output filename (without extension)

        Returns:
            Path to written file
        """
        output_path = self.output_dir / f"{filename}.parquet"
        df.to_parquet(output_path, index=False, engine="pyarrow")
        logger.info(f"Wrote {len(df)} rows to {output_path}")
        return output_path

    def write(
        self,
        df: pd.DataFrame,
        filename: str,
        format: Optional[str] = None,
    ) -> Path:
        """
        Write DataFrame to file in specified format.

        Args:
            df: DataFrame to write
            filename: Output filename (without extension)
            format: Output format (csv, json, or parquet), defaults to settings

        Returns:
            Path to written file
        """
        format = format or settings.output_format

        if format == "csv":
            return self.write_csv(df, filename)
        elif format == "json":
            return self.write_json(df, filename)
        elif format == "parquet":
            return self.write_parquet(df, filename)
        else:
            raise ValueError(f"Unsupported output format: {format}")


class DataReader:
    """Read data from various input formats."""

    @staticmethod
    def read_csv(file_path: Path) -> pd.DataFrame:
        """
        Read CSV file into DataFrame.

        Args:
            file_path: Path to CSV file

        Returns:
            DataFrame with file contents
        """
        df = pd.read_csv(file_path)
        logger.info(f"Read {len(df)} rows from {file_path}")
        return df

    @staticmethod
    def read_json(file_path: Path) -> pd.DataFrame:
        """
        Read JSON file into DataFrame.

        Args:
            file_path: Path to JSON file

        Returns:
            DataFrame with file contents
        """
        df = pd.read_json(file_path, orient="records")
        logger.info(f"Read {len(df)} rows from {file_path}")
        return df

    @staticmethod
    def read_parquet(file_path: Path) -> pd.DataFrame:
        """
        Read Parquet file into DataFrame.

        Args:
            file_path: Path to Parquet file

        Returns:
            DataFrame with file contents
        """
        df = pd.read_parquet(file_path, engine="pyarrow")
        logger.info(f"Read {len(df)} rows from {file_path}")
        return df
