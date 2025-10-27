"""
FastAPI REST API for DuckParqStream
Provides endpoints for ingestion, querying, and management
"""
from fastapi import FastAPI, HTTPException, UploadFile, File, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime
import json
import logging

from config import API_HOST, API_PORT, API_TITLE, API_VERSION
from ingestion import ingestion_engine
from query_engine import query_engine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI
app = FastAPI(
    title=API_TITLE,
    version=API_VERSION,
    description="High-performance local JSON storage with DuckDB + Parquet"
)

# CORS middleware for web interface
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# Request/Response Models
# ============================================================================

class IngestRecordRequest(BaseModel):
    """Single or batch record ingestion"""
    records: List[Dict[str, Any]] = Field(
        ...,
        description="JSON records to ingest",
        example=[{"id": "123", "name": "test", "value": 42}]
    )
    data_date: Optional[str] = Field(
        None,
        description="Date this data belongs to (YYYY-MM-DD or ISO format). Defaults to current date.",
        example="2025-10-15"
    )
    data_type: str = Field(
        default="default",
        description="Type of data (log, event, transaction, etc.)",
        example="log"
    )


class QueryByIDRequest(BaseModel):
    """Query by record ID"""
    record_id: str = Field(..., example="abc123")


class QueryByDateRequest(BaseModel):
    """Query by date range"""
    start_date: str = Field(..., example="2025-10-01")
    end_date: str = Field(..., example="2025-10-28")
    limit: int = Field(default=100, le=10000)


class SQLQueryRequest(BaseModel):
    """Raw SQL query"""
    query: str = Field(
        ...,
        example="SELECT * FROM all_records LIMIT 10"
    )
    limit: Optional[int] = Field(default=None, le=10000)


class SearchRequest(BaseModel):
    """Full-text search"""
    search_term: str = Field(..., example="test")
    column: Optional[str] = Field(None, example="name")
    limit: int = Field(default=100, le=10000)


# ============================================================================
# Health & Info Endpoints
# ============================================================================

@app.get("/")
async def root():
    """API root endpoint"""
    return {
        "name": API_TITLE,
        "version": API_VERSION,
        "status": "operational",
        "timestamp": datetime.now().isoformat(),
        "endpoints": {
            "docs": "/docs",
            "health": "/health",
            "statistics": "/statistics"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Test database connection
        stats = query_engine.get_statistics()

        return {
            "status": "healthy",
            "database": "connected",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e)
            }
        )


@app.get("/statistics")
async def get_statistics():
    """Get comprehensive dataset statistics"""
    try:
        # Get query engine stats
        stats = query_engine.get_statistics()

        # Get file stats
        file_stats = ingestion_engine.get_file_stats()

        return {
            "status": "success",
            "query_statistics": stats.get("statistics", {}),
            "file_statistics": file_stats,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Statistics error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Ingestion Endpoints
# ============================================================================

@app.post("/ingest")
async def ingest_records(request: IngestRecordRequest):
    """
    Ingest JSON records into Parquet storage

    Supports single records or batches.
    Data is automatically partitioned by date range and type.

    Example request:
    ```json
    {
        "records": [{"id": "123", "name": "test"}],
        "data_date": "2025-10-15",
        "data_type": "log"
    }
    ```

    This will store in: `2025/10/log_01_20.parquet`
    """
    try:
        # Parse data_date if provided
        from datetime import datetime
        data_date = None
        if request.data_date:
            try:
                # Try parsing ISO format first
                data_date = datetime.fromisoformat(request.data_date.replace('Z', '+00:00'))
            except:
                # Try YYYY-MM-DD format
                data_date = datetime.strptime(request.data_date, '%Y-%m-%d')

        result = ingestion_engine.append_to_parquet(
            request.records,
            data_date=data_date,
            data_type=request.data_type
        )

        if result["status"] == "error":
            raise HTTPException(status_code=400, detail=result["message"])

        return result

    except ValueError as e:
        logger.error(f"Date parsing error: {e}")
        raise HTTPException(status_code=400, detail=f"Invalid date format: {str(e)}")
    except Exception as e:
        logger.error(f"Ingestion error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/ingest/file")
async def ingest_file(file: UploadFile = File(...)):
    """
    Ingest JSON/JSONL file

    Supports:
    - JSON array: [{"id": 1}, {"id": 2}]
    - JSONL: One JSON object per line
    """
    try:
        content = await file.read()
        content_str = content.decode('utf-8')

        # Try parsing as JSON array
        try:
            records = json.loads(content_str)
            if not isinstance(records, list):
                records = [records]
        except json.JSONDecodeError:
            # Try JSONL format
            records = []
            for line in content_str.strip().split('\n'):
                if line.strip():
                    records.append(json.loads(line))

        result = ingestion_engine.append_to_parquet(records)

        if result["status"] == "error":
            raise HTTPException(status_code=400, detail=result["message"])

        return result

    except Exception as e:
        logger.error(f"File ingestion error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Query Endpoints
# ============================================================================

@app.post("/query/sql")
async def query_sql(request: SQLQueryRequest):
    """
    Execute raw SQL query

    Query against the `all_records` view which includes all Parquet files.

    Example:
    ```sql
    SELECT * FROM all_records
    WHERE ingested_at >= '2025-10-01'
    LIMIT 100
    ```
    """
    try:
        result = query_engine.execute_sql(request.query, request.limit)

        if result["status"] == "error":
            raise HTTPException(status_code=400, detail=result["message"])

        return result

    except Exception as e:
        logger.error(f"SQL query error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/query/id/{record_id}")
async def query_by_id(record_id: str):
    """Query record by ID"""
    try:
        result = query_engine.query_by_id(record_id)

        if result["status"] == "error":
            raise HTTPException(status_code=400, detail=result["message"])

        if result["row_count"] == 0:
            raise HTTPException(status_code=404, detail="Record not found")

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"ID query error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/query/date-range")
async def query_date_range(request: QueryByDateRequest):
    """Query records within date range"""
    try:
        result = query_engine.query_by_date_range(
            request.start_date,
            request.end_date,
            request.limit
        )

        if result["status"] == "error":
            raise HTTPException(status_code=400, detail=result["message"])

        return result

    except Exception as e:
        logger.error(f"Date range query error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/query/recent")
async def query_recent(
    hours: int = Query(default=24, ge=1, le=168),
    limit: int = Query(default=100, le=10000)
):
    """Query records from last N hours (default: 24)"""
    try:
        result = query_engine.query_recent(hours, limit)

        if result["status"] == "error":
            raise HTTPException(status_code=400, detail=result["message"])

        return result

    except Exception as e:
        logger.error(f"Recent query error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/query/search")
async def search_records(request: SearchRequest):
    """
    Full-text search across records

    Searches all text columns if no specific column provided.
    """
    try:
        result = query_engine.search(
            request.search_term,
            request.column,
            request.limit
        )

        if result["status"] == "error":
            raise HTTPException(status_code=400, detail=result["message"])

        return result

    except Exception as e:
        logger.error(f"Search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Management Endpoints
# ============================================================================

@app.get("/files")
async def list_files():
    """List all Parquet files with metadata"""
    try:
        files = ingestion_engine.get_file_stats()
        return {
            "status": "success",
            "files": files,
            "total_files": len(files)
        }
    except Exception as e:
        logger.error(f"File list error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/schema")
async def get_schema():
    """Get current data schema"""
    try:
        result = query_engine.execute_sql("DESCRIBE all_records")

        if result["status"] == "error":
            return {
                "status": "no_data",
                "message": "No data ingested yet"
            }

        return {
            "status": "success",
            "schema": result["data"]
        }
    except Exception as e:
        logger.error(f"Schema error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Run Server
# ============================================================================

if __name__ == "__main__":
    import uvicorn

    logger.info(f"🚀 Starting {API_TITLE} v{API_VERSION}")
    logger.info(f"📍 API: http://{API_HOST}:{API_PORT}")
    logger.info(f"📚 Docs: http://{API_HOST}:{API_PORT}/docs")

    uvicorn.run(
        app,
        host=API_HOST,
        port=API_PORT,
        log_level="info"
    )
