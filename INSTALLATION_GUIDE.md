# Installation & Testing Guide

This guide will walk you through installation, testing, and using your new DuckParqStream database.

---

## Prerequisites

- **Python 3.8+** (Check: `python --version`)
- **pip** (Usually comes with Python)
- **Windows, macOS, or Linux**

---

## Step 1: Verify Installation

### Check Python
```bash
python --version
# Should show: Python 3.8 or higher
```

### Navigate to Project
```bash
cd C:\Users\siam\PROJECTS\DuckParqStream
```

---

## Step 2: Install Dependencies

```bash
pip install -r requirements.txt
```

This installs:
- `duckdb` - Database engine
- `pyarrow` - Parquet file handling
- `pandas` - Data manipulation
- `fastapi` - REST API framework
- `uvicorn` - ASGI server

**Expected output:** Successfully installed 5-8 packages

---

## Step 3: Test the System

### Option A: Run Complete Examples (Recommended)

```bash
python example.py
```

This will:
1. Create test database
2. Ingest 10,003 records
3. Run various queries
4. Show statistics
5. Demonstrate all features

**Expected time:** 5-10 seconds

**Expected output:**
```
============================================================
  🦆 DuckParqStream - Complete Examples
============================================================

✅ Ingested 3 records
✅ Ingested 10,000 records
✅ Query executed: 30,012 total records
✅ Statistics: 0.58 MB storage
✅ All Examples Completed!
```

### Option B: Start Web Interface

```bash
python run.py
```

**What happens:**
1. Server starts on `http://localhost:8000`
2. Browser opens automatically
3. Web UI loads with all features

**What you can do:**
- Generate test data (click "Generate Test Data")
- Write SQL queries
- Upload JSON files
- View statistics

---

## Step 4: Verify Everything Works

### Check Data Files
```bash
# Windows
dir data\parquet\*.parquet

# Linux/Mac
ls -lh data/parquet/*.parquet
```

**Expected:** You should see `data_2025_wXX.parquet` files

### Check Statistics
```bash
python run.py stats
```

**Expected output:**
```
📊 Dataset Statistics
============================================================

📁 Parquet Files: 1
  - data_2025_w44.parquet: 30,012 rows, 0.58 MB

📈 Total Records: 30,012
📅 Date Range: 2025-10-27 to 2025-10-27
```

### Test API
```bash
# While server is running (python run.py)
curl http://localhost:8000/health
```

**Expected:**
```json
{
  "status": "healthy",
  "database": "connected"
}
```

---

## Step 5: Quick Feature Tour

### 1. Ingest Your First Custom Data

Open the web interface (`http://localhost:8000`) and:

1. Go to **"Data Ingestion"** panel
2. Click **"JSON Records"** tab
3. Paste this:
```json
[
  {
    "id": "my_first_record",
    "name": "Test User",
    "value": 100
  }
]
```
4. Click **"Ingest Records"**

**Expected:** ✅ Ingested 1 record

### 2. Query Your Data

1. Go to **"Query Data"** panel
2. Click **"SQL Query"** tab
3. Enter:
```sql
SELECT * FROM all_records WHERE id = 'my_first_record'
```
4. Click **"Execute Query"**

**Expected:** Your record displayed in the results panel

### 3. View Statistics

1. Click **"Refresh Statistics"** button
2. See:
   - Total records
   - File count
   - Storage size
   - Status

---

## Common Issues & Solutions

### Issue 1: "Module not found"
```
ModuleNotFoundError: No module named 'duckdb'
```

**Solution:**
```bash
pip install -r requirements.txt
```

### Issue 2: "Permission denied"
```
PermissionError: [Errno 13] Permission denied: 'data/parquet'
```

**Solution:** Ensure you have write permissions to the project directory

### Issue 3: "Port already in use"
```
Error: Port 8000 is already in use
```

**Solution 1:** Stop other process using port 8000
**Solution 2:** Change port in `backend/config.py`:
```python
API_PORT = 8001
```

### Issue 4: "No data showing in queries"

**Solution:**
```bash
# Check if data exists
python run.py stats

# If no data, generate some
python run.py generate --count 1000
```

### Issue 5: Browser doesn't open automatically

**Solution:** Manually open: `http://localhost:8000`
Or access the UI directly: Open `frontend/index.html` in your browser

---

## Windows Users: Easy Start

Double-click `start.bat` for an interactive menu:

```
1. Start Web Interface
2. Run Examples
3. Generate Test Data
4. View Statistics
5. Exit
```

---

## Advanced Testing

### Test 1: High Volume Ingestion

```bash
python run.py generate --type user --count 100000
```

**Expected:** 100,000 records ingested in 1-2 seconds

### Test 2: Complex SQL Query

```python
python -c "
from backend.query_engine import query_engine
result = query_engine.execute_sql('''
    SELECT
        country,
        COUNT(*) as users,
        ROUND(AVG(balance), 2) as avg_balance
    FROM all_records
    WHERE balance > 1000
    GROUP BY country
    ORDER BY users DESC
''')
print(result['data'])
"
```

### Test 3: API Endpoint

```bash
# Ingest via API
curl -X POST http://localhost:8000/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "records": [
      {"id": "api_test", "name": "API Test", "value": 42}
    ]
  }'
```

### Test 4: File Upload

```bash
# Create test file
echo '[{"id":"file_test","name":"File Test"}]' > test.json

# Upload (requires server running)
curl -X POST http://localhost:8000/ingest/file \
  -F "file=@test.json"
```

---

## Performance Testing

### Benchmark Ingestion Speed

```python
import time
from backend.ingestion import ingestion_engine
from backend.test_data_generator import TestDataGenerator

generator = TestDataGenerator()
records = generator.generate_batch('user', count=50000)

start = time.time()
result = ingestion_engine.append_to_parquet(records)
duration = time.time() - start

print(f"Ingested {result['records_processed']} records in {duration:.2f}s")
print(f"Speed: {result['records_processed']/duration:.0f} records/sec")
```

**Expected:** 10,000+ records/second

### Benchmark Query Speed

```python
import time
from backend.query_engine import query_engine

start = time.time()
result = query_engine.execute_sql("SELECT COUNT(*) FROM all_records")
duration = time.time() - start

print(f"Query took {duration:.3f} seconds")
print(f"Result: {result['data'][0]}")
```

**Expected:** < 0.1 seconds for simple queries

---

## Verification Checklist

✅ Dependencies installed
✅ Example script runs successfully
✅ Web interface loads
✅ Can ingest data
✅ Can query data
✅ Statistics show correct data
✅ API endpoints respond
✅ Files created in `data/parquet/`

---

## Next Steps

Once everything works:

1. **Read the full docs:** `README.md`
2. **Try your own data:** Upload JSON files
3. **Explore SQL:** Run complex queries
4. **Set up continuous ingestion:** Connect to your API
5. **Customize:** Edit `backend/config.py`

---

## Getting Help

### Documentation
- `README.md` - Full documentation
- `QUICKSTART.md` - Quick start guide
- `PROJECT_SUMMARY.md` - Feature overview
- API Docs: `http://localhost:8000/docs` (when server running)

### Logs
```bash
# Check logs directory
ls logs/
```

### Debug Mode
```python
# Edit backend/config.py
import logging
logging.basicConfig(level=logging.DEBUG)
```

---

## Success Indicators

You're ready to use DuckParqStream when:

✅ `python example.py` completes without errors
✅ Web UI loads and responds
✅ You can ingest and query data
✅ Statistics show your data
✅ API endpoints return valid JSON

**Congratulations! Your local JSON database is ready to use! 🎉**
