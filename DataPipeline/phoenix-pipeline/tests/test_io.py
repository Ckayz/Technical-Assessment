"""Tests for input/output module."""

import json
import pytest
from pathlib import Path
import pandas as pd

from phoenix_pipeline.io import StateManager, DataWriter, DataReader


class TestStateManager:
    """Test suite for StateManager."""

    def test_load_state_no_file(self, temp_state_file: Path) -> None:
        """Test loading state when file doesn't exist."""
        state_manager = StateManager(temp_state_file)
        state = state_manager.load_state()

        assert state["last_processed_block"] == 0

    def test_save_and_load_state(self, temp_state_file: Path) -> None:
        """Test saving and loading state."""
        state_manager = StateManager(temp_state_file)

        test_state = {"last_processed_block": 12345, "custom_field": "test"}
        state_manager.save_state(test_state)

        loaded_state = state_manager.load_state()
        assert loaded_state["last_processed_block"] == 12345
        assert loaded_state["custom_field"] == "test"

    def test_update_last_processed_block(self, temp_state_file: Path) -> None:
        """Test updating last processed block."""
        state_manager = StateManager(temp_state_file)

        state_manager.update_last_processed_block(5000)
        block = state_manager.get_last_processed_block()

        assert block == 5000

    def test_get_last_processed_block_default(self, temp_state_file: Path) -> None:
        """Test getting last processed block with no state file."""
        state_manager = StateManager(temp_state_file)
        block = state_manager.get_last_processed_block()

        assert block == 0


class TestDataWriter:
    """Test suite for DataWriter."""

    def test_write_csv(self, sample_dataframe: pd.DataFrame, temp_output_dir: Path) -> None:
        """Test writing CSV file."""
        writer = DataWriter(temp_output_dir)
        output_path = writer.write_csv(sample_dataframe, "test_swaps")

        assert output_path.exists()
        assert output_path.suffix == ".csv"

        # Verify content
        df_read = pd.read_csv(output_path)
        assert len(df_read) == len(sample_dataframe)

    def test_write_json(self, sample_dataframe: pd.DataFrame, temp_output_dir: Path) -> None:
        """Test writing JSON file."""
        writer = DataWriter(temp_output_dir)
        output_path = writer.write_json(sample_dataframe, "test_swaps")

        assert output_path.exists()
        assert output_path.suffix == ".json"

        # Verify content
        with open(output_path) as f:
            data = json.load(f)
        assert len(data) == len(sample_dataframe)

    def test_write_parquet(self, sample_dataframe: pd.DataFrame, temp_output_dir: Path) -> None:
        """Test writing Parquet file."""
        writer = DataWriter(temp_output_dir)
        output_path = writer.write_parquet(sample_dataframe, "test_swaps")

        assert output_path.exists()
        assert output_path.suffix == ".parquet"

        # Verify content
        df_read = pd.read_parquet(output_path)
        assert len(df_read) == len(sample_dataframe)

    def test_write_auto_format(self, sample_dataframe: pd.DataFrame, temp_output_dir: Path) -> None:
        """Test writing with auto format detection."""
        writer = DataWriter(temp_output_dir)
        output_path = writer.write(sample_dataframe, "test_swaps", format="json")

        assert output_path.exists()
        assert output_path.suffix == ".json"

    def test_write_invalid_format(self, sample_dataframe: pd.DataFrame, temp_output_dir: Path) -> None:
        """Test writing with invalid format."""
        writer = DataWriter(temp_output_dir)

        with pytest.raises(ValueError):
            writer.write(sample_dataframe, "test_swaps", format="invalid")


class TestDataReader:
    """Test suite for DataReader."""

    def test_read_csv(self, sample_dataframe: pd.DataFrame, temp_output_dir: Path) -> None:
        """Test reading CSV file."""
        # Write file first
        file_path = temp_output_dir / "test.csv"
        sample_dataframe.to_csv(file_path, index=False)

        # Read and verify
        df = DataReader.read_csv(file_path)
        assert len(df) == len(sample_dataframe)

    def test_read_json(self, sample_dataframe: pd.DataFrame, temp_output_dir: Path) -> None:
        """Test reading JSON file."""
        # Write file first
        file_path = temp_output_dir / "test.json"
        sample_dataframe.to_json(file_path, orient="records")

        # Read and verify
        df = DataReader.read_json(file_path)
        assert len(df) == len(sample_dataframe)

    def test_read_parquet(self, sample_dataframe: pd.DataFrame, temp_output_dir: Path) -> None:
        """Test reading Parquet file."""
        # Write file first
        file_path = temp_output_dir / "test.parquet"
        sample_dataframe.to_parquet(file_path, index=False)

        # Read and verify
        df = DataReader.read_parquet(file_path)
        assert len(df) == len(sample_dataframe)
