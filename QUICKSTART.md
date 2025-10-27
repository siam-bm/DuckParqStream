# 🚀 Quick Start Guide

Get up and running with DuckParqStream in 3 minutes!

---

## Step 1: Install Dependencies (30 seconds)

```bash
pip install -r requirements.txt
```

---

## Step 2: Start the Server (10 seconds)

```bash
python run.py
```

Your browser will automatically open to the web interface!

---

## Step 3: Generate Test Data (20 seconds)

In the web interface, click **"Generate Test Data"** tab and click **"Generate & Ingest"**.

Or from command line:

```bash
# In another terminal
python run.py generate --type user --count 5000
```

---

## Step 4: Query Your Data (30 seconds)

### Option A: Web Interface

1. Click the **"Query Data"** panel
2. Use the pre-filled SQL query
3. Click **"Execute Query"**

### Option B: Command Line

```python
python -c "
from backend.query_engine import query_engine
result = query_engine.execute_sql('SELECT * FROM all_records LIMIT 10')
print(result['data'])
"
```

---

## 🎉 You're Done!

You now have a fully functional local JSON database!

### What's Next?

1. **Ingest Your Own Data**
   - Use the JSON input tab
   - Or upload a JSON/JSONL file
   - Or use the API: `http://localhost:8000/docs`

2. **Try Advanced Queries**
```sql
-- Count records by week
SELECT
  DATE_TRUNC('week', ingested_at) as week,
  COUNT(*) as count
FROM all_records
GROUP BY week
ORDER BY week DESC;

-- Find records by status
SELECT * FROM all_records
WHERE status = 'active'
LIMIT 100;

-- Search for specific values
SELECT * FROM all_records
WHERE CAST(value AS INT) > 500;
```

3. **Check Statistics**
```bash
python run.py stats
```

4. **Continuous Ingestion**
   - Set up a webhook pointing to `http://localhost:8000/ingest`
   - Or poll an API periodically
   - Or stream data using the Python API

---

## 📱 Quick API Examples

### Ingest Data
```bash
curl -X POST http://localhost:8000/ingest \
  -H "Content-Type: application/json" \
  -d '{"records": [{"id": "1", "name": "test"}]}'
```

### Query Recent Data
```bash
curl http://localhost:8000/query/recent?hours=24&limit=10
```

### Search
```bash
curl -X POST http://localhost:8000/query/search \
  -H "Content-Type: application/json" \
  -d '{"search_term": "test", "limit": 10}'
```

### Get Statistics
```bash
curl http://localhost:8000/statistics
```

---

## 🎯 Common Tasks

### Daily Data Collection Job

```python
# collect_data.py
import requests
from backend.ingestion import ingestion_engine

# Fetch from your API
response = requests.get("https://api.example.com/data")
data = response.json()

# Ingest
result = ingestion_engine.append_to_parquet(data)
print(f"✅ Ingested {result['records_processed']} records")
```

Schedule with cron (Linux/Mac):
```bash
# Run every hour
0 * * * * cd /path/to/DuckParqStream && python collect_data.py
```

Or Windows Task Scheduler:
```bash
# Create scheduled task
schtasks /create /tn "DuckParqStream Ingest" /tr "python C:\path\to\DuckParqStream\collect_data.py" /sc hourly
```

---

## 💡 Tips

1. **Performance**: DuckDB is blazing fast. Try querying millions of records!

2. **Storage**: Parquet compression is excellent. 1M JSON records (~500MB) → ~50MB Parquet

3. **Rotation**: Files rotate weekly automatically. Archive old files to `data/archive/` when needed

4. **Queries**: Use the full power of SQL - JOINs, aggregations, window functions all work!

5. **Schema**: Don't worry about schema changes. Parquet handles evolution automatically.

---

## 🆘 Troubleshooting

**"No module named X"**
```bash
pip install -r requirements.txt
```

**"No data showing"**
```bash
python run.py stats  # Check if data exists
```

**"Port already in use"**
- Edit `backend/config.py` and change `API_PORT = 8001`

**"Permission denied"**
- Ensure you have write access to the `data/` directory

---

## 📖 Full Documentation

See [README.md](README.md) for comprehensive documentation.

---

**Ready to handle millions of records! 🦆**
