"""
Configuration settings for DuckParqStream
"""
import os
from pathlib import Path

# Base paths
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data" / "parquet"
ARCHIVE_DIR = BASE_DIR / "data" / "archive"
LOGS_DIR = BASE_DIR / "logs"
DUCKDB_FILE = BASE_DIR / "data" / "local_data.duckdb"

# Ensure directories exist
DATA_DIR.mkdir(parents=True, exist_ok=True)
ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)

# Parquet settings
COMPRESSION = 'zstd'  # Options: snappy, gzip, zstd, lz4
ROW_GROUP_SIZE = 100000  # Rows per group for optimal performance

# Date-based partitioning (year/month/type_fromDay_toDay.parquet)
PARTITION_BY_DATE_RANGE = True
DATE_FIELD = 'data_date'  # The date from client (when data is for)
INGESTED_AT_FIELD = 'ingested_at'  # When we received it
ID_FIELD = 'record_id'
TYPE_FIELD = 'data_type'  # Type of data from client

# Size-based partitioning settings
MAX_ROWS_PER_FILE = 100  # Maximum rows per file before creating new file
# When file reaches limit, new file created starting from overflow date
# Example: log_01_05.parquet (100 rows) → overflow on day 5 → create log_05_30.parquet

# API settings
API_HOST = "0.0.0.0"
API_PORT = 8000
API_TITLE = "DuckParqStream API"
API_VERSION = "1.0.0"

# Query limits
MAX_QUERY_RESULTS = 10000
DEFAULT_LIMIT = 100

# Performance tuning
DUCKDB_MEMORY_LIMIT = "2GB"
DUCKDB_THREADS = 4
