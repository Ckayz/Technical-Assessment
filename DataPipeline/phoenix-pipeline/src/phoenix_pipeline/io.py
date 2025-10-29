"""Input/output operations for reading and writing data."""

import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional

import pandas as pd

from phoenix_pipeline.config import settings

logger = logging.getLogger(__name__)


class StateManager:
    """Manage pipeline state for tracking progress."""

    def __init__(self, state_file: Optional[Path] = None) -> None:
        """
        Initialize state manager.

        Args:
            state_file: Path to state file (defaults to settings)
        """
        self.state_file = state_file or settings.state_file
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
