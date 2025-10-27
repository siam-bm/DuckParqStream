# 🦆 DuckParqStream

**High-Performance Local JSON Database with DuckDB + Parquet**

A complete solution for storing and querying millions of JSON records locally without external databases or hosting costs. Features automatic weekly rotation, blazing-fast SQL queries, and a beautiful web interface.

---

## ✨ Features

- 🚀 **Lightning Fast**: Query millions of records in seconds with DuckDB
- 💾 **Local Storage**: No external databases, all data stored in compressed Parquet files
- 📅 **Weekly Rotation**: Automatic file partitioning for easy data management
- 🔍 **Powerful Queries**: Full SQL support with DuckDB
- 🌐 **Web Interface**: Beautiful, modern UI for data ingestion and querying
- 📊 **Real-time Stats**: Monitor record counts, file sizes, and data distribution
- 🔄 **Streaming Support**: Continuous ingestion from APIs or data streams
- 💰 **Zero Cost**: No hosting, no subscriptions, completely free

---

## 🏗️ Architecture

```
JSON Records → Parquet Files (weekly) → DuckDB Engine → Fast Queries
                    ↓
            Compressed Storage
           (10x smaller than JSON)
```

**Technology Stack:**
- **DuckDB**: Embedded analytical SQL engine
- **Parquet**: Columnar storage with excellent compression
- **FastAPI**: Modern REST API framework
- **Vanilla JS**: Lightweight web interface

---

## 📦 Installation

### Prerequisites
- Python 3.8 or higher
- pip

### Setup

1. **Clone or download this project**

2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

That's it! No database installation, no configuration files.

---

## 🚀 Quick Start

### Start the Server

```bash
python run.py
```

This will:
- Start the API server on `http://localhost:8000`
- Open the web interface automatically
- Display API documentation at `http://localhost:8000/docs`

### Generate Test Data

```bash
# Generate 1,000 user records
python run.py generate --type user --count 1000

# Generate 10,000 transaction records
python run.py generate --type transaction --count 10000

# Other types: event, product, sensor
```

### View Statistics

```bash
python run.py stats
```

---

## 💻 Usage

### Web Interface

The web interface provides everything you need:

1. **Data Ingestion**
   - Paste JSON directly
   - Upload JSON/JSONL files
   - Generate test data

2. **Query Data**
   - Execute SQL queries
   - Search by ID
   - Filter by date range
   - Full-text search

3. **Monitoring**
   - Real-time statistics
   - File management
   - Schema inspection

### API Usage

#### Ingest Records

```bash
curl -X POST http://localhost:8000/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "records": [
      {"id": "123", "name": "John", "value": 42},
      {"id": "124", "name": "Jane", "value": 99}
    ]
  }'
```

#### Query with SQL

```bash
curl -X POST http://localhost:8000/query/sql \
  -H "Content-Type: application/json" \
  -d '{
    "query": "SELECT * FROM all_records LIMIT 10"
  }'
```

#### Query by Date Range

```bash
curl -X POST http://localhost:8000/query/date-range \
  -H "Content-Type: application/json" \
  -d '{
    "start_date": "2025-10-01",
    "end_date": "2025-10-28",
    "limit": 100
  }'
```

#### Query Recent Data

```bash
curl http://localhost:8000/query/recent?hours=24&limit=100
```

#### Search Records

```bash
curl -X POST http://localhost:8000/query/search \
  -H "Content-Type: application/json" \
  -d '{
    "search_term": "john",
    "limit": 100
  }'
```

---

## 📚 Python API

### Ingestion

```python
from backend.ingestion import ingestion_engine

# Ingest records
records = [
    {"id": "123", "name": "John", "value": 42},
    {"id": "124", "name": "Jane", "value": 99}
]

result = ingestion_engine.append_to_parquet(records)
print(f"Ingested {result['records_processed']} records")
```

### Querying

```python
from backend.query_engine import query_engine

# SQL query
result = query_engine.execute_sql(
    "SELECT * FROM all_records WHERE value > 50 LIMIT 10"
)

# Query by ID
result = query_engine.query_by_id("123")

# Query by date range
result = query_engine.query_by_date_range(
    "2025-10-01",
    "2025-10-28",
    limit=100
)

# Search
result = query_engine.search("john", limit=100)

# Statistics
stats = query_engine.get_statistics()
```

---

## 📊 Performance

| Data Size | Query Time (filtered) | Storage Size |
|-----------|----------------------|--------------|
| 10M rows  | < 1 second          | ~100 MB      |
| 100M rows | 1-5 seconds         | ~1 GB        |
| 1B+ rows  | Fast with partitions| ~10 GB       |

**Compression:** Parquet with ZSTD typically achieves 10x compression vs JSON.

---

## 🗂️ Data Organization

### Weekly Partitioning

Files are automatically organized by week:

```
data/parquet/
  ├── data_2025_w43.parquet  (Week 43)
  ├── data_2025_w44.parquet  (Week 44)
  └── data_2025_w45.parquet  (Week 45)
```

### Archival

Move old files to archive:

```bash
mv data/parquet/data_2025_w43.parquet data/archive/
```

DuckDB will automatically query only active files.

---

## 🔧 Configuration

Edit `backend/config.py`:

```python
# Compression: snappy, gzip, zstd, lz4
COMPRESSION = 'zstd'

# Performance tuning
DUCKDB_MEMORY_LIMIT = "2GB"
DUCKDB_THREADS = 4

# Query limits
MAX_QUERY_RESULTS = 10000
DEFAULT_LIMIT = 100
```

---

## 📝 Example Queries

### Basic Queries

```sql
-- All records
SELECT * FROM all_records LIMIT 10;

-- Filter by date
SELECT * FROM all_records
WHERE ingested_at >= '2025-10-01'
LIMIT 100;

-- Count records
SELECT COUNT(*) FROM all_records;

-- Group by week
SELECT
  DATE_TRUNC('week', ingested_at) as week,
  COUNT(*) as count
FROM all_records
GROUP BY week
ORDER BY week DESC;
```

### Advanced Analytics

```sql
-- Top users by value
SELECT
  user_id,
  SUM(value) as total_value,
  COUNT(*) as transaction_count
FROM all_records
GROUP BY user_id
ORDER BY total_value DESC
LIMIT 10;

-- Daily aggregates
SELECT
  DATE_TRUNC('day', ingested_at) as day,
  AVG(value) as avg_value,
  MAX(value) as max_value,
  COUNT(*) as count
FROM all_records
GROUP BY day
ORDER BY day DESC;

-- Search nested JSON
SELECT * FROM all_records
WHERE metadata->>'status' = 'active';
```

---

## 🔄 Continuous Ingestion

### Stream from API

```python
import requests
from backend.ingestion import ingestion_engine

def stream_from_api(api_url, batch_size=1000):
    """Stream data from API and ingest in batches"""
    batch = []

    while True:
        response = requests.get(api_url)
        data = response.json()

        batch.extend(data)

        if len(batch) >= batch_size:
            result = ingestion_engine.append_to_parquet(batch)
            print(f"Ingested {result['records_processed']} records")
            batch = []

# Usage
stream_from_api("https://api.example.com/data")
```

### Scheduled Ingestion

```python
import schedule
import time

def ingest_job():
    # Fetch and ingest data
    pass

# Run every hour
schedule.every().hour.do(ingest_job)

while True:
    schedule.run_pending()
    time.sleep(60)
```

---

## 🧪 Testing

### Generate Large Dataset

```bash
# Generate 1 million records
python backend/test_data_generator.py --type user --count 1000000 --output test_data/large.json
```

### Benchmark Queries

```python
from backend.query_engine import query_engine
import time

start = time.time()
result = query_engine.execute_sql("SELECT COUNT(*) FROM all_records")
duration = time.time() - start

print(f"Query took {duration:.3f} seconds")
```

---

## 🐛 Troubleshooting

### No Data Showing

1. Check if data was ingested:
```bash
python run.py stats
```

2. Verify Parquet files exist:
```bash
ls data/parquet/
```

3. Check API logs for errors

### Query Errors

- Ensure `all_records` view exists (auto-created)
- Check column names with: `DESCRIBE all_records`
- Verify date format: ISO 8601 (`YYYY-MM-DD`)

### Performance Issues

- Reduce `DUCKDB_MEMORY_LIMIT` if system has low RAM
- Increase `DUCKDB_THREADS` for better parallelism
- Archive old Parquet files to reduce scan time

---

## 📂 Project Structure

```
DuckParqStream/
├── backend/
│   ├── api.py                  # FastAPI REST API
│   ├── config.py               # Configuration
│   ├── ingestion.py            # Data ingestion engine
│   ├── query_engine.py         # DuckDB query engine
│   └── test_data_generator.py  # Test data generator
├── frontend/
│   └── index.html              # Web interface
├── data/
│   ├── parquet/                # Active Parquet files
│   ├── archive/                # Archived files
│   └── local_data.duckdb       # DuckDB database
├── run.py                      # Main entry point
├── requirements.txt            # Python dependencies
└── README.md                   # This file
```

---

## 🎯 Use Cases

- **Log Aggregation**: Store and analyze application logs
- **API Data Collection**: Continuously fetch and store API data
- **Event Tracking**: Store user events and analytics
- **IoT Data**: Time-series sensor data storage
- **Data Archival**: Local backup of JSON data with querying
- **ETL Pipeline**: Local staging for data transformations

---

## 🔮 Advanced Features

### Custom Partitioning

Modify `get_weekly_filename()` in `backend/ingestion.py`:

```python
def get_weekly_filename(self, timestamp=None):
    ts = timestamp or datetime.now(timezone.utc)
    # Daily partitioning
    return self.data_dir / f"data_{ts.strftime('%Y_%m_%d')}.parquet"
```

### Schema Evolution

Parquet handles schema changes automatically. New columns are added, missing columns default to NULL.

### Export Data

```python
# Export to CSV
query_engine.connection.execute("""
    COPY (SELECT * FROM all_records)
    TO 'export.csv' (HEADER, DELIMITER ',')
""")

# Export to JSON
result = query_engine.execute_sql("SELECT * FROM all_records")
import json
with open('export.json', 'w') as f:
    json.dump(result['data'], f)
```

---

## 🤝 Contributing

Contributions welcome! Areas for improvement:
- Additional query templates
- Enhanced visualization
- Background job scheduling
- Data validation rules
- Export formats

---

## 📄 License

MIT License - Free for personal and commercial use

---

## 🙏 Acknowledgments

Built with:
- [DuckDB](https://duckdb.org/) - Embedded analytical database
- [Apache Parquet](https://parquet.apache.org/) - Columnar storage format
- [FastAPI](https://fastapi.tiangolo.com/) - Modern API framework

---

## 📞 Support

Issues? Questions? Ideas?
- Check the `/docs` endpoint for API documentation
- Review example queries in this README
- Test with small datasets first

---

**Happy querying! 🦆**
