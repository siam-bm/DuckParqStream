"""
Core data ingestion module for JSON to Parquet conversion
Handles weekly rotation and efficient append operations
"""
import json
import pandas as pd
import pyarrow.parquet as pq
import pyarrow as pa
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging
from config import (
    DATA_DIR, COMPRESSION, ROW_GROUP_SIZE,
    DATE_FIELD, INGESTED_AT_FIELD, ID_FIELD, TYPE_FIELD,
    PARTITION_BY_DATE_RANGE, MAX_ROWS_PER_FILE
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ParquetIngestionEngine:
    """Handles JSON ingestion with date-range based Parquet partitioning"""

    def __init__(self, data_dir: Path = DATA_DIR):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def find_or_create_file_for_date(
        self,
        data_date: datetime,
        data_type: str = "default",
        new_record_count: int = 0
    ) -> Path:
        """
        Find existing file that can accommodate this date or create new one
        Uses size-based partitioning with sequential date ranges

        Logic:
        1. Check existing files in year/month for this type
        2. If file exists and has space (< MAX_ROWS_PER_FILE), return it
        3. If file is full, create new file starting from this date
        4. Update previous file's end date to last record's date

        Structure: year/month/type_fromDay_toDay.parquet
        Example: log_01_05.parquet (100 rows, days 1-5)
                 → overflow → log_05_30.parquet (new file from day 5)

        Args:
            data_date: The date this data belongs to
            data_type: Type of data (log, event, transaction, etc.)

        Returns:
            Path object for the parquet file
        """
        import calendar

        year = data_date.year
        month = data_date.month
        day = data_date.day

        # Create directory structure: year/month/
        year_month_dir = self.data_dir / str(year) / f"{month:02d}"
        year_month_dir.mkdir(parents=True, exist_ok=True)

        # Sanitize data_type
        safe_type = "".join(c for c in data_type if c.isalnum() or c in ('_', '-')).lower()
        if not safe_type:
            safe_type = "default"

        # Find all existing files for this type in this month
        existing_files = sorted(year_month_dir.glob(f"{safe_type}_*.parquet"))

        last_day_of_month = calendar.monthrange(year, month)[1]

        # Check if we can use an existing file
        for file_path in existing_files:
            # Parse filename: type_fromDay_toDay.parquet
            parts = file_path.stem.split('_')
            if len(parts) >= 3:
                try:
                    from_day = int(parts[-2])
                    to_day = int(parts[-1])

                    # Check if this date falls in this file's range
                    if from_day <= day <= to_day:
                        # Check if file has space
                        try:
                            existing_table = pq.read_table(file_path)
                            current_rows = existing_table.num_rows

                            # Check if adding new records would exceed limit
                            if current_rows + new_record_count <= MAX_ROWS_PER_FILE:
                                # File has space
                                return file_path
                            else:
                                # File is full - need to create new file
                                # Get the last date in current file
                                df = existing_table.to_pandas()
                                if DATE_FIELD in df.columns:
                                    last_date_in_file = pd.to_datetime(df[DATE_FIELD]).max()
                                    actual_last_day = last_date_in_file.day

                                    # Rename current file to actual range
                                    new_name = f"{safe_type}_{from_day:02d}_{actual_last_day:02d}.parquet"
                                    new_path = file_path.parent / new_name
                                    if file_path != new_path:
                                        file_path.rename(new_path)
                                        logger.info(f"Renamed {file_path.name} → {new_name}")

                                    # Create new file starting from current day
                                    new_file = year_month_dir / f"{safe_type}_{day:02d}_{last_day_of_month:02d}.parquet"
                                    return new_file
                        except Exception as e:
                            logger.warning(f"Error reading {file_path}: {e}")
                            continue

                except (ValueError, IndexError):
                    continue

        # No suitable file found - create new one
        # Determine start day (current day)
        new_file = year_month_dir / f"{safe_type}_{day:02d}_{last_day_of_month:02d}.parquet"
        return new_file

    def normalize_json_record(
        self,
        record: Dict[str, Any],
        data_date: Optional[datetime] = None,
        data_type: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Normalize nested JSON to flat structure
        Adds metadata fields for tracking

        Args:
            record: JSON record(s) to normalize
            data_date: The date this data belongs to (from client)
            data_type: Type of data (from client)
        """
        # Handle both single record and list
        if not isinstance(record, list):
            record = [record]

        # Flatten nested structures
        df = pd.json_normalize(record)

        # Add data_date (the date this data is FOR)
        if data_date:
            df[DATE_FIELD] = data_date
        elif DATE_FIELD not in df.columns:
            # If client didn't provide date, use current date
            df[DATE_FIELD] = datetime.now(timezone.utc)

        # Add ingested_at (when WE received it)
        df[INGESTED_AT_FIELD] = datetime.now(timezone.utc)

        # Add data_type
        if data_type:
            df[TYPE_FIELD] = data_type
        elif TYPE_FIELD not in df.columns:
            df[TYPE_FIELD] = 'default'

        # Ensure ID field exists
        if ID_FIELD not in df.columns:
            if 'id' in df.columns:
                df[ID_FIELD] = df['id']
            else:
                # Generate UUID if no ID present
                import uuid
                df[ID_FIELD] = [str(uuid.uuid4()) for _ in range(len(df))]

        return df

    def append_to_parquet(
        self,
        records: List[Dict[str, Any]],
        data_date: Optional[datetime] = None,
        data_type: str = "default",
        batch_size: int = 1000
    ) -> Dict[str, Any]:
        """
        Append JSON records to date-range partitioned Parquet file

        Args:
            records: List of JSON records to append
            data_date: The date this data belongs to (from client)
            data_type: Type of data (log, event, transaction, etc.)
            batch_size: Number of records to batch before writing

        Returns:
            Status dictionary with ingestion metrics
        """
        try:
            start_time = datetime.now(timezone.utc)

            # Use current date if not provided
            if data_date is None:
                data_date = datetime.now(timezone.utc)

            # Normalize records with date and type
            df = self.normalize_json_record(records, data_date, data_type)

            if df.empty:
                return {
                    "status": "error",
                    "message": "No valid records to ingest",
                    "records_processed": 0
                }

            # Get target file based on date, type, and size limits
            target_file = self.find_or_create_file_for_date(data_date, data_type, len(df))

            # Convert to Arrow table
            table = pa.Table.from_pandas(df)

            # Append or create
            if target_file.exists():
                # Read existing and append with schema unification
                existing = pq.read_table(target_file)

                # Unify schemas by adding missing columns as null
                existing_schema = existing.schema
                new_schema = table.schema

                # Get all unique column names
                all_columns = set(existing_schema.names) | set(new_schema.names)

                # Add missing columns to existing table
                for col in new_schema.names:
                    if col not in existing_schema.names:
                        # Add null column with correct type
                        null_array = pa.nulls(len(existing), type=table.schema.field(col).type)
                        existing = existing.append_column(col, null_array)

                # Add missing columns to new table
                for col in existing_schema.names:
                    if col not in new_schema.names:
                        # Add null column with correct type
                        null_array = pa.nulls(len(table), type=existing.schema.field(col).type)
                        table = table.append_column(col, null_array)

                # Now concat with unified schemas
                table = pa.concat_tables([existing, table], promote=True)

            # Write with compression
            pq.write_table(
                table,
                target_file,
                compression=COMPRESSION,
                row_group_size=ROW_GROUP_SIZE
            )

            duration = (datetime.now(timezone.utc) - start_time).total_seconds()
            file_size = target_file.stat().st_size / (1024 * 1024)  # MB

            logger.info(
                f"✅ Ingested {len(df)} records to {target_file.name} "
                f"({file_size:.2f}MB) in {duration:.2f}s"
            )

            return {
                "status": "success",
                "records_processed": len(df),
                "file": str(target_file.name),
                "file_size_mb": round(file_size, 2),
                "duration_seconds": round(duration, 2),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }

        except Exception as e:
            logger.error(f"❌ Ingestion failed: {str(e)}")
            return {
                "status": "error",
                "message": str(e),
                "records_processed": 0
            }

    def get_file_stats(self) -> List[Dict[str, Any]]:
        """Get statistics for all Parquet files"""
        stats = []

        for file_path in sorted(self.data_dir.glob("*.parquet")):
            try:
                table = pq.read_table(file_path)
                file_size = file_path.stat().st_size / (1024 * 1024)

                stats.append({
                    "filename": file_path.name,
                    "row_count": table.num_rows,
                    "file_size_mb": round(file_size, 2),
                    "columns": table.column_names,
                    "modified": datetime.fromtimestamp(
                        file_path.stat().st_mtime
                    ).isoformat()
                })
            except Exception as e:
                logger.error(f"Error reading {file_path}: {e}")

        return stats

    def batch_ingest(
        self,
        json_file_path: Path,
        chunk_size: int = 10000
    ) -> Dict[str, Any]:
        """
        Ingest large JSON file in batches

        Args:
            json_file_path: Path to JSON or JSONL file
            chunk_size: Records per batch
        """
        total_processed = 0
        errors = 0

        try:
            with open(json_file_path, 'r') as f:
                # Try JSONL format first
                batch = []
                for line_num, line in enumerate(f, 1):
                    try:
                        record = json.loads(line.strip())
                        batch.append(record)

                        if len(batch) >= chunk_size:
                            result = self.append_to_parquet(batch)
                            if result["status"] == "success":
                                total_processed += result["records_processed"]
                            else:
                                errors += 1
                            batch = []

                    except json.JSONDecodeError:
                        # Maybe it's a single JSON array
                        f.seek(0)
                        data = json.load(f)
                        if isinstance(data, list):
                            result = self.append_to_parquet(data)
                            return result
                        break

                # Process remaining batch
                if batch:
                    result = self.append_to_parquet(batch)
                    if result["status"] == "success":
                        total_processed += result["records_processed"]

            return {
                "status": "success",
                "total_records": total_processed,
                "errors": errors
            }

        except Exception as e:
            return {
                "status": "error",
                "message": str(e)
            }


# Singleton instance
ingestion_engine = ParquetIngestionEngine()
