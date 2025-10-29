# Phoenix Pipeline

A robust data pipeline for fetching, enriching, and aggregating Phoenix DEX swap data from The Graph subgraph, with price enrichment from CoinGecko API.

## Features

- Fetch swap events from Phoenix DEX subgraph
- Enrich data with real-time cryptocurrency prices from CoinGecko
- Transform and aggregate swap data with pandas
- Export to multiple formats (CSV, JSON, Parquet)
- State management for incremental processing
- Robust error handling with automatic retries
- Rate limiting for API compliance
- Comprehensive test coverage
- Type-safe with mypy

## Project Structure

```
phoenix-pipeline/
├── src/
│   └── phoenix_pipeline/
│       ├── __init__.py
│       ├── config.py          # Configuration management with Pydantic
│       ├── subgraph.py         # GraphQL client for Phoenix subgraph
│       ├── coingecko.py        # CoinGecko API client
│       ├── transform.py        # Data transformation and aggregation
│       ├── io.py               # File I/O and state management
│       └── main.py             # Main orchestrator
├── tests/                      # Test suite
│   ├── conftest.py
│   ├── test_config.py
│   ├── test_transform.py
│   └── test_io.py
├── pyproject.toml              # Project dependencies and configuration
├── .env.example                # Example environment configuration
└── README.md
```

## Setup

### Prerequisites

- Python 3.11 or higher
- [uv](https://github.com/astral-sh/uv) (recommended) or pip

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd phoenix-pipeline
```

2. Install uv (if not already installed):
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

3. Create a virtual environment and install dependencies:
```bash
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install -e .
```

4. Install development dependencies (for testing):
```bash
uv pip install -e ".[dev]"
```

5. Copy the example environment file and configure:
```bash
cp .env.example .env
```

Edit `.env` with your configuration (see [Configuration](#configuration) below).

## Configuration

### Environment Variables

Configure the pipeline by setting environment variables in your `.env` file:

#### Phoenix Subgraph

| Variable | Description | Default |
|----------|-------------|---------|
| `SUBGRAPH_URL` | Phoenix subgraph GraphQL endpoint | `https://api.thegraph.com/subgraphs/name/phoenix/dex` |
| `SUBGRAPH_TIMEOUT` | Request timeout in seconds | `30` |
| `SUBGRAPH_MAX_RETRIES` | Maximum retry attempts | `3` |

#### CoinGecko API

| Variable | Description | Default |
|----------|-------------|---------|
| `COINGECKO_API_URL` | CoinGecko API base URL | `https://api.coingecko.com/api/v3` |
| `COINGECKO_API_KEY` | API key for higher rate limits (optional) | `None` |
| `COINGECKO_TIMEOUT` | Request timeout in seconds | `30` |
| `COINGECKO_MAX_RETRIES` | Maximum retry attempts | `3` |
| `COINGECKO_RATE_LIMIT_DELAY` | Delay between requests in seconds | `1.2` |

#### Pipeline Settings

| Variable | Description | Default |
|----------|-------------|---------|
| `BATCH_SIZE` | Records to process per batch | `100` |
| `START_BLOCK` | Starting block number | `0` |
| `END_BLOCK` | Ending block number (empty = latest) | `None` |

#### Output Settings

| Variable | Description | Default |
|----------|-------------|---------|
| `OUTPUT_DIR` | Output directory path | `output` |
| `OUTPUT_FORMAT` | Output format: `csv`, `json`, or `parquet` | `csv` |
| `STATE_FILE` | State file for tracking progress | `output/state.json` |
| `LOG_LEVEL` | Logging level | `INFO` |

## Usage

### Basic Usage

Run the pipeline with default settings:

```bash
python -m phoenix_pipeline.main
```

Or use the installed entry point:

```bash
phoenix-pipeline
```

### Sample Commands

1. **Fetch swaps from a specific block range:**
```bash
START_BLOCK=1000 END_BLOCK=2000 python -m phoenix_pipeline.main
```

2. **Output as JSON instead of CSV:**
```bash
OUTPUT_FORMAT=json python -m phoenix_pipeline.main
```

3. **Use larger batch size for faster processing:**
```bash
BATCH_SIZE=500 python -m phoenix_pipeline.main
```

4. **Enable debug logging:**
```bash
LOG_LEVEL=DEBUG python -m phoenix_pipeline.main
```

5. **Resume from last processed block:**
The pipeline automatically resumes from the last processed block stored in the state file. To start fresh, delete the state file:
```bash
rm output/state.json
python -m phoenix_pipeline.main
```

### Programmatic Usage

```python
from phoenix_pipeline.main import PhoenixPipeline

# Create and run pipeline
pipeline = PhoenixPipeline()
pipeline.run(start_block=1000, end_block=2000, resume=False)
```

### Using Individual Modules

```python
from phoenix_pipeline.subgraph import SubgraphClient
from phoenix_pipeline.coingecko import CoinGeckoClient
from phoenix_pipeline.transform import DataTransformer

# Fetch swaps
with SubgraphClient() as client:
    swaps = client.get_swaps(start_block=1000, first=100)

# Transform data
transformer = DataTransformer()
df = transformer.normalize_swaps(swaps)
df = transformer.validate_data(df)

# Get prices
with CoinGeckoClient() as client:
    prices = client.get_price(["bitcoin", "ethereum"])
```

## Design Decisions

### Idempotency

The pipeline is designed to be idempotent and resumable:

- **State Management**: Tracks the last successfully processed block in `state.json`
- **Resume Capability**: Automatically resumes from the last checkpoint on restart
- **Deduplication**: Removes duplicate swap records based on transaction ID
- **Validation**: Filters out invalid records (null values, negative amounts)

This allows you to:
- Safely re-run the pipeline without reprocessing data
- Resume after failures or interruptions
- Run incremental updates on a schedule

### Rate Limiting

To comply with API rate limits and avoid throttling:

- **CoinGecko**: 1.2-second delay between requests (configurable via `COINGECKO_RATE_LIMIT_DELAY`)
- **Free tier**: ~50 calls/minute
- **Pro tier**: Use `COINGECKO_API_KEY` for higher limits
- **The Graph**: No built-in rate limiting (relies on subgraph endpoint limits)

### Retry Logic

Robust error handling with exponential backoff:

- **Automatic Retries**: All API calls retry up to 3 times (configurable)
- **Exponential Backoff**: Wait time increases: 2s, 4s, 8s (up to 10s max)
- **Retry Conditions**: Retries on network errors, timeouts, and HTTP 5xx errors
- **Circuit Breaking**: Stops retrying after max attempts and raises exception

### Data Validation

Ensures data quality through multiple stages:

1. **Type Conversion**: Converts string values to appropriate numeric/datetime types
2. **Null Handling**: Removes records with missing critical fields
3. **Range Validation**: Filters negative amounts and invalid timestamps
4. **Deduplication**: Removes duplicate transactions
5. **Outlier Detection**: Identifies anomalous values using z-score method

### Batch Processing

Efficient processing of large datasets:

- **Pagination**: Fetches data in configurable batches (default 100 records)
- **Memory Efficient**: Processes and writes data incrementally
- **State Checkpoints**: Saves progress after each batch
- **Graceful Shutdown**: Handles interruptions without data loss

### Error Handling

Comprehensive error handling strategy:

- **Graceful Degradation**: Continues processing on non-critical errors
- **Detailed Logging**: Logs all errors with context for debugging
- **Partial Success**: Saves successfully processed data before failure
- **State Consistency**: Always maintains valid state file

## Testing

Run the test suite:

```bash
pytest
```

Run with coverage report:

```bash
pytest --cov=src/phoenix_pipeline --cov-report=html
```

Run type checking:

```bash
mypy src/phoenix_pipeline
```

Run all checks:

```bash
pytest && mypy src/phoenix_pipeline
```

## Output Files

The pipeline generates the following files in the output directory:

### Data Files

- `swaps_YYYYMMDD_HHMMSS.csv/json/parquet`: Detailed swap data with enrichment
- `aggregations_YYYYMMDD_HHMMSS.csv/json/parquet`: Aggregated metrics by date and token

### State File

- `state.json`: Tracks pipeline progress
```json
{
  "last_processed_block": 12345,
  "last_updated": "2024-01-15T10:30:00"
}
```

## Troubleshooting

### Rate Limit Errors

If you encounter rate limit errors from CoinGecko:
- Increase `COINGECKO_RATE_LIMIT_DELAY` (e.g., to 2.0 seconds)
- Obtain a CoinGecko Pro API key and set `COINGECKO_API_KEY`
- Reduce batch size with `BATCH_SIZE`

### Subgraph Timeout

If subgraph queries timeout:
- Increase `SUBGRAPH_TIMEOUT` (e.g., to 60 seconds)
- Reduce `BATCH_SIZE` to fetch fewer records per request
- Check subgraph health and availability

### Memory Issues

For large datasets:
- Reduce `BATCH_SIZE` to process smaller chunks
- Use `parquet` format instead of CSV for better compression
- Process data in smaller block ranges

### State File Corruption

If the state file becomes corrupted:
```bash
rm output/state.json
python -m phoenix_pipeline.main
```

## Performance Tips

1. **Use Parquet**: 50-80% smaller files and faster read/write
   ```bash
   OUTPUT_FORMAT=parquet python -m phoenix_pipeline.main
   ```

2. **Increase Batch Size**: Process more records per request (if memory allows)
   ```bash
   BATCH_SIZE=500 python -m phoenix_pipeline.main
   ```

3. **Parallel Processing**: For very large datasets, split by block ranges and run in parallel

4. **CoinGecko Pro**: Use API key for 5x higher rate limits

## Development

### Code Style

The project uses:
- Type hints throughout (enforced by mypy)
- Docstrings for all public functions
- PEP 8 style guide

### Adding New Features

1. Add functionality to appropriate module (`subgraph.py`, `transform.py`, etc.)
2. Add comprehensive tests in `tests/`
3. Update type hints and docstrings
4. Run tests and type checking
5. Update README if adding user-facing features

## License

MIT License - see LICENSE file for details

## Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass and type checking succeeds
5. Submit a pull request

## Support

For issues and questions:
- Open an issue on GitHub
- Check existing issues for solutions
- Review logs with `LOG_LEVEL=DEBUG` for detailed information
