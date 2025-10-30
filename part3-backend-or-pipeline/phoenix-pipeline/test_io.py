"""Test script for I/O functions."""

import logging
import tempfile
from pathlib import Path

import pandas as pd

from phoenix_pipeline import io

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def test_read_write_state():
    """Test read_state and write_state functions."""
    logger.info("=" * 80)
    logger.info("Test 1: read_state() and write_state()")
    logger.info("=" * 80)

    with tempfile.TemporaryDirectory() as tmpdir:
        state_path = Path(tmpdir) / "test_state.json"

        # Test 1: Read non-existent state (should return default)
        state = io.read_state(state_path)
        logger.info(f"  Default state: {state}")
        assert state["last_processed_block"] == 0, "Default block should be 0"
        logger.info("  ✓ Default state loaded correctly")

        # Test 2: Write state
        io.write_state(state_path, block=18000000, extra_field="test_value")
        logger.info("  ✓ State written")

        # Test 3: Read written state
        state = io.read_state(state_path)
        logger.info(f"  Read state: {state}")
        assert state["last_processed_block"] == 18000000, "Block should be 18000000"
        assert state["extra_field"] == "test_value", "Extra field should be preserved"
        assert "last_updated" in state, "Should have last_updated field"
        logger.info("  ✓ State read correctly")

        # Test 4: Update state (should merge with existing)
        io.write_state(state_path, block=18000100, another_field="another_value")
        state = io.read_state(state_path)
        assert state["last_processed_block"] == 18000100, "Block should be updated"
        assert state["extra_field"] == "test_value", "Old fields should be preserved"
        assert state["another_field"] == "another_value", "New fields should be added"
        logger.info("  ✓ State merging works correctly")


def test_write_json():
    """Test write_json function."""
    logger.info("\n" + "=" * 80)
    logger.info("Test 2: write_json()")
    logger.info("=" * 80)

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)

        # Test 1: Write dictionary
        dict_path = tmpdir_path / "test_dict.json"
        test_dict = {"key1": "value1", "key2": 123, "key3": [1, 2, 3]}
        io.write_json(dict_path, test_dict)
        logger.info("  ✓ Dictionary written")

        # Verify
        import json
        with open(dict_path) as f:
            loaded = json.load(f)
        assert loaded == test_dict, "Loaded dict should match original"
        logger.info("  ✓ Dictionary verified")

        # Test 2: Write list
        list_path = tmpdir_path / "test_list.json"
        test_list = [{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}]
        io.write_json(list_path, test_list)
        logger.info("  ✓ List written")

        # Verify
        with open(list_path) as f:
            loaded = json.load(f)
        assert loaded == test_list, "Loaded list should match original"
        logger.info("  ✓ List verified")


def test_write_csv():
    """Test write_csv function."""
    logger.info("\n" + "=" * 80)
    logger.info("Test 3: write_csv()")
    logger.info("=" * 80)

    with tempfile.TemporaryDirectory() as tmpdir:
        csv_path = Path(tmpdir) / "test.csv"

        # Create test DataFrame
        df = pd.DataFrame({
            "a": [1, 2, 3],
            "b": ["x", "y", "z"],
            "c": [1.1, 2.2, 3.3],
        })

        # Write CSV
        io.write_csv(csv_path, df)
        logger.info("  ✓ CSV written")

        # Verify
        loaded_df = pd.read_csv(csv_path)
        assert loaded_df.equals(df), "Loaded DataFrame should match original"
        logger.info("  ✓ CSV verified")


def test_filter_swaps_by_block():
    """Test filter_swaps_by_block function."""
    logger.info("\n" + "=" * 80)
    logger.info("Test 4: filter_swaps_by_block()")
    logger.info("=" * 80)

    # Test with list
    swaps_list = [
        {"blockNumber": 100, "data": "old"},
        {"blockNumber": 200, "data": "new"},
        {"blockNumber": 150, "data": "middle"},
    ]

    filtered = io.filter_swaps_by_block(swaps_list, 150)
    logger.info(f"  Filtered list: {len(swaps_list)} -> {len(filtered)} swaps")
    assert len(filtered) == 1, "Should have 1 swap > block 150"
    assert filtered[0]["blockNumber"] == 200, "Should keep block 200"
    logger.info("  ✓ List filtering works")

    # Test with DataFrame
    swaps_df = pd.DataFrame(swaps_list)
    filtered_df = io.filter_swaps_by_block(swaps_df, 150)
    logger.info(f"  Filtered DataFrame: {len(swaps_df)} -> {len(filtered_df)} rows")
    assert len(filtered_df) == 1, "Should have 1 row > block 150"
    assert filtered_df.iloc[0]["blockNumber"] == 200, "Should keep block 200"
    logger.info("  ✓ DataFrame filtering works")

    # Test with all swaps already processed
    filtered = io.filter_swaps_by_block(swaps_list, 300)
    assert len(filtered) == 0, "Should filter all swaps"
    logger.info("  ✓ Complete filtering works")


def test_compute_data_hash():
    """Test compute_data_hash function."""
    logger.info("\n" + "=" * 80)
    logger.info("Test 5: compute_data_hash()")
    logger.info("=" * 80)

    # Test with DataFrame
    df1 = pd.DataFrame({"a": [1, 2], "b": [3, 4]})
    df2 = pd.DataFrame({"a": [1, 2], "b": [3, 4]})
    df3 = pd.DataFrame({"a": [1, 2], "b": [3, 5]})  # Different

    hash1 = io.compute_data_hash(df1)
    hash2 = io.compute_data_hash(df2)
    hash3 = io.compute_data_hash(df3)

    logger.info(f"  Hash 1: {hash1[:16]}...")
    logger.info(f"  Hash 2: {hash2[:16]}...")
    logger.info(f"  Hash 3: {hash3[:16]}...")

    assert hash1 == hash2, "Identical DataFrames should have same hash"
    assert hash1 != hash3, "Different DataFrames should have different hash"
    logger.info("  ✓ DataFrame hashing works")

    # Test with dict
    dict1 = {"key": "value", "num": 123}
    dict2 = {"num": 123, "key": "value"}  # Different order
    dict3 = {"key": "value", "num": 124}  # Different value

    hash1 = io.compute_data_hash(dict1)
    hash2 = io.compute_data_hash(dict2)
    hash3 = io.compute_data_hash(dict3)

    assert hash1 == hash2, "Dicts with same content (different order) should have same hash"
    assert hash1 != hash3, "Different dicts should have different hash"
    logger.info("  ✓ Dict hashing works")


def test_write_with_hash():
    """Test write_with_hash for idempotency."""
    logger.info("\n" + "=" * 80)
    logger.info("Test 6: write_with_hash() - Idempotency")
    logger.info("=" * 80)

    with tempfile.TemporaryDirectory() as tmpdir:
        csv_path = Path(tmpdir) / "output.csv"

        df1 = pd.DataFrame({"a": [1, 2], "b": [3, 4]})
        df2 = pd.DataFrame({"a": [1, 2], "b": [3, 4]})  # Same data
        df3 = pd.DataFrame({"a": [1, 2], "b": [3, 5]})  # Different data

        # First write
        written = io.write_with_hash(csv_path, df1, format="csv")
        assert written is True, "First write should return True"
        logger.info("  ✓ First write succeeded")

        # Second write (same data) - should skip
        written = io.write_with_hash(csv_path, df2, format="csv")
        assert written is False, "Second write should return False (skipped)"
        logger.info("  ✓ Second write skipped (data unchanged)")

        # Third write (different data) - should write
        written = io.write_with_hash(csv_path, df3, format="csv")
        assert written is True, "Third write should return True (data changed)"
        logger.info("  ✓ Third write succeeded (data changed)")

        # Verify hash file exists
        hash_path = Path(str(csv_path) + ".hash")
        assert hash_path.exists(), "Hash file should exist"
        logger.info("  ✓ Hash file created")


def test_directory_creation():
    """Test that OUTPUT_DIR is created automatically."""
    logger.info("\n" + "=" * 80)
    logger.info("Test 7: Automatic Directory Creation")
    logger.info("=" * 80)

    with tempfile.TemporaryDirectory() as tmpdir:
        # Test nested directory creation
        nested_path = Path(tmpdir) / "level1" / "level2" / "output.csv"

        df = pd.DataFrame({"a": [1, 2]})
        io.write_csv(nested_path, df)

        assert nested_path.exists(), "File should be created"
        assert nested_path.parent.exists(), "Parent directories should be created"
        logger.info("  ✓ Nested directories created automatically")

        # Test with write_json
        json_path = Path(tmpdir) / "another" / "path" / "output.json"
        io.write_json(json_path, {"key": "value"})

        assert json_path.exists(), "JSON file should be created"
        logger.info("  ✓ JSON directory creation works")

        # Test with write_state
        state_path = Path(tmpdir) / "deep" / "state" / "state.json"
        io.write_state(state_path, block=100)

        assert state_path.exists(), "State file should be created"
        logger.info("  ✓ State directory creation works")


def test_integration_workflow():
    """Test full idempotent workflow."""
    logger.info("\n" + "=" * 80)
    logger.info("Test 8: Integration - Idempotent Workflow")
    logger.info("=" * 80)

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        state_path = tmpdir_path / "state.json"
        output_path = tmpdir_path / "swaps.csv"

        # Simulate first run
        logger.info("\n--- Run 1 ---")
        state = io.read_state(state_path)
        last_block = state["last_processed_block"]
        logger.info(f"  Last processed block: {last_block}")

        # Simulate fetching swaps
        all_swaps = pd.DataFrame({
            "blockNumber": [100, 200, 300, 400],
            "txHash": ["0xa", "0xb", "0xc", "0xd"],
        })

        # Filter by last processed block
        new_swaps = io.filter_swaps_by_block(all_swaps, last_block)
        logger.info(f"  New swaps: {len(new_swaps)}")

        # Write swaps
        written = io.write_with_hash(output_path, new_swaps, format="csv")
        logger.info(f"  Written: {written}")

        # Update state
        max_block = int(new_swaps["blockNumber"].max())
        io.write_state(state_path, block=max_block)
        logger.info(f"  Updated state to block {max_block}")

        # Simulate second run (no new data)
        logger.info("\n--- Run 2 (No New Data) ---")
        state = io.read_state(state_path)
        last_block = state["last_processed_block"]
        logger.info(f"  Last processed block: {last_block}")

        # Same swaps
        new_swaps = io.filter_swaps_by_block(all_swaps, last_block)
        logger.info(f"  New swaps: {len(new_swaps)}")
        assert len(new_swaps) == 0, "Should have no new swaps"

        # Simulate third run (with new swaps)
        logger.info("\n--- Run 3 (New Data) ---")
        all_swaps_updated = pd.DataFrame({
            "blockNumber": [100, 200, 300, 400, 500, 600],
            "txHash": ["0xa", "0xb", "0xc", "0xd", "0xe", "0xf"],
        })

        new_swaps = io.filter_swaps_by_block(all_swaps_updated, last_block)
        logger.info(f"  New swaps: {len(new_swaps)}")
        assert len(new_swaps) == 2, "Should have 2 new swaps (500, 600)"

        # Write and update
        written = io.write_with_hash(output_path, new_swaps, format="csv")
        logger.info(f"  Written: {written}")
        assert written is True, "Should write new data"

        max_block = int(new_swaps["blockNumber"].max())
        io.write_state(state_path, block=max_block)
        logger.info(f"  Updated state to block {max_block}")

        logger.info("\n  ✓ Idempotent workflow completed successfully")


def main():
    """Run all I/O tests."""
    try:
        test_read_write_state()
        test_write_json()
        test_write_csv()
        test_filter_swaps_by_block()
        test_compute_data_hash()
        test_write_with_hash()
        test_directory_creation()
        test_integration_workflow()

        logger.info("\n" + "=" * 80)
        logger.info("All I/O Tests Passed!")
        logger.info("=" * 80)

        logger.info("\nImplementation Features Verified:")
        logger.info("  ✓ read_state() returns dict with last_processed_block (default 0)")
        logger.info("  ✓ write_state() writes block and merges with existing state")
        logger.info("  ✓ write_json() accepts dict/list data")
        logger.info("  ✓ write_csv() writes DataFrame")
        logger.info("  ✓ filter_swaps_by_block() implements idempotency")
        logger.info("  ✓ compute_data_hash() for change detection")
        logger.info("  ✓ write_with_hash() skips unchanged data")
        logger.info("  ✓ OUTPUT_DIR created automatically")
        logger.info("  ✓ Full idempotent workflow works")

    except AssertionError as e:
        logger.error(f"Test failed: {e}", exc_info=True)
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    main()
