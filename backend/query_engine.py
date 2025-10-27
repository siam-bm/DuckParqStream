"""
DuckDB query engine for efficient Parquet querying
Supports SQL and high-level query interfaces
"""
import duckdb
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import pandas as pd
import logging
from config import (
    DATA_DIR, DUCKDB_FILE, DUCKDB_MEMORY_LIMIT,
    DUCKDB_THREADS, MAX_QUERY_RESULTS, DEFAULT_LIMIT,
    DATE_FIELD, ID_FIELD, TYPE_FIELD
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DuckDBQueryEngine:
    """High-performance query engine for Parquet data"""

    def __init__(self, db_file: Path = DUCKDB_FILE, data_dir: Path = DATA_DIR):
        self.db_file = Path(db_file)
        self.data_dir = Path(data_dir)
        self.connection = None
        self._connect()

    def _connect(self):
        """Establish DuckDB connection with optimization"""
        try:
            self.connection = duckdb.connect(str(self.db_file))

            # Performance tuning
            self.connection.execute(f"SET memory_limit='{DUCKDB_MEMORY_LIMIT}'")
            self.connection.execute(f"SET threads TO {DUCKDB_THREADS}")
            self.connection.execute("SET enable_progress_bar=true")

            # Register all Parquet files as a view
            self._register_parquet_view()

            logger.info(f"✅ DuckDB connected: {self.db_file}")

        except Exception as e:
            logger.error(f"❌ DuckDB connection failed: {e}")
            raise

    def _get_parquet_files_for_range(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        data_type: Optional[str] = None
    ) -> List[Path]:
        """
        Find relevant Parquet files based on date range and type
        Uses directory structure: year/month/type_fromDay_toDay.parquet
        """
        files = []

        # If no filters, get all parquet files recursively
        if not start_date and not end_date and not data_type:
            files = list(self.data_dir.rglob("*.parquet"))
            return files

        # Walk through the directory structure
        for year_dir in self.data_dir.iterdir():
            if not year_dir.is_dir():
                continue

            try:
                year = int(year_dir.name)
            except ValueError:
                continue

            # Check if year is in range
            if start_date and year < start_date.year:
                continue
            if end_date and year > end_date.year:
                continue

            for month_dir in year_dir.iterdir():
                if not month_dir.is_dir():
                    continue

                try:
                    month = int(month_dir.name)
                except ValueError:
                    continue

                # Check if month is in range
                if start_date and (year == start_date.year and month < start_date.month):
                    continue
                if end_date and (year == end_date.year and month > end_date.month):
                    continue

                # Get parquet files in this month
                for parquet_file in month_dir.glob("*.parquet"):
                    # Filter by type if specified
                    if data_type:
                        # Filename format: type_fromDay_toDay.parquet
                        file_type = parquet_file.stem.split('_')[0]
                        if file_type != data_type.lower():
                            continue

                    files.append(parquet_file)

        return files

    def _register_parquet_view(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        data_type: Optional[str] = None
    ):
        """
        Create view pointing to relevant Parquet files
        Intelligently filters based on date range and type
        """
        # Get relevant files
        files = self._get_parquet_files_for_range(start_date, end_date, data_type)

        if not files:
            logger.warning("⚠️ No Parquet files found for specified criteria")
            return

        # Create pattern for DuckDB
        if len(files) == 1:
            parquet_pattern = str(files[0]).replace('\\', '/')
        else:
            # Use list of files for efficiency
            file_list = [str(f).replace('\\', '/') for f in files]
            parquet_pattern = "['" + "','".join(file_list) + "']"

        try:
            self.connection.execute(f"""
                CREATE OR REPLACE VIEW all_records AS
                SELECT * FROM read_parquet({parquet_pattern})
            """)

            logger.info(f"📊 Registered {len(files)} Parquet file(s)")
        except Exception as e:
            logger.error(f"Failed to register view: {e}")
            # Fallback to recursive glob
            parquet_pattern = str(self.data_dir / "**" / "*.parquet").replace('\\', '/')
            self.connection.execute(f"""
                CREATE OR REPLACE VIEW all_records AS
                SELECT * FROM read_parquet('{parquet_pattern}')
            """)
            logger.info(f"📊 Registered Parquet view (recursive): {parquet_pattern}")

    def execute_sql(
        self,
        query: str,
        limit: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Execute raw SQL query

        Args:
            query: SQL query string
            limit: Optional result limit

        Returns:
            Query results with metadata
        """
        try:
            # Refresh view to handle schema changes
            self._register_parquet_view()

            start_time = datetime.now()

            # Add safety limit if not present
            if limit and "LIMIT" not in query.upper():
                query = f"{query.rstrip(';')} LIMIT {limit}"

            result = self.connection.execute(query).fetchdf()

            duration = (datetime.now() - start_time).total_seconds()

            return {
                "status": "success",
                "data": result.to_dict(orient='records'),
                "row_count": len(result),
                "columns": list(result.columns),
                "duration_seconds": round(duration, 3),
                "query": query
            }

        except Exception as e:
            logger.error(f"❌ Query failed: {e}")
            return {
                "status": "error",
                "message": str(e),
                "query": query
            }

    def query_by_id(self, record_id: str) -> Dict[str, Any]:
        """Query single record by ID"""
        query = f"""
            SELECT * FROM all_records
            WHERE {ID_FIELD} = '{record_id}'
            LIMIT 1
        """
        return self.execute_sql(query)

    def query_by_date_range(
        self,
        start_date: str,
        end_date: str,
        limit: int = DEFAULT_LIMIT
    ) -> Dict[str, Any]:
        """
        Query records within date range

        Args:
            start_date: ISO format date (e.g., '2025-10-01')
            end_date: ISO format date
            limit: Maximum records to return
        """
        query = f"""
            SELECT * FROM all_records
            WHERE {DATE_FIELD} >= '{start_date}'
              AND {DATE_FIELD} < '{end_date}'
            ORDER BY {DATE_FIELD} DESC
            LIMIT {limit}
        """
        return self.execute_sql(query)

    def query_recent(
        self,
        hours: int = 24,
        limit: int = DEFAULT_LIMIT
    ) -> Dict[str, Any]:
        """Query records from last N hours"""
        query = f"""
            SELECT * FROM all_records
            WHERE {DATE_FIELD} >= NOW() - INTERVAL '{hours} hours'
            ORDER BY {DATE_FIELD} DESC
            LIMIT {limit}
        """
        return self.execute_sql(query)

    def get_statistics(self) -> Dict[str, Any]:
        """Get comprehensive dataset statistics"""
        try:
            # Refresh view to include new files
            self._register_parquet_view()

            stats = {}

            # Total records
            total_query = "SELECT COUNT(*) as total FROM all_records"
            total_result = self.connection.execute(total_query).fetchone()
            stats['total_records'] = total_result[0] if total_result else 0

            if stats['total_records'] == 0:
                return {
                    "status": "success",
                    "statistics": {
                        "total_records": 0,
                        "message": "No data available yet"
                    }
                }

            # Date range
            date_query = f"""
                SELECT
                    MIN({DATE_FIELD}) as earliest,
                    MAX({DATE_FIELD}) as latest
                FROM all_records
            """
            date_result = self.connection.execute(date_query).fetchone()
            stats['date_range'] = {
                'earliest': str(date_result[0]),
                'latest': str(date_result[1])
            }

            # Weekly distribution
            weekly_query = f"""
                SELECT
                    DATE_TRUNC('week', {DATE_FIELD}) as week,
                    COUNT(*) as count
                FROM all_records
                GROUP BY week
                ORDER BY week DESC
                LIMIT 10
            """
            weekly_result = self.connection.execute(weekly_query).fetchdf()
            stats['weekly_distribution'] = weekly_result.to_dict(orient='records')

            # Column info
            columns_query = "DESCRIBE all_records"
            columns_result = self.connection.execute(columns_query).fetchdf()
            stats['schema'] = columns_result.to_dict(orient='records')

            return {
                "status": "success",
                "statistics": stats
            }

        except Exception as e:
            logger.error(f"❌ Statistics query failed: {e}")
            return {
                "status": "error",
                "message": str(e)
            }

    def search(
        self,
        search_term: str,
        column: str = None,
        limit: int = DEFAULT_LIMIT
    ) -> Dict[str, Any]:
        """
        Full-text search across records

        Args:
            search_term: Text to search for
            column: Specific column to search (None = all columns)
            limit: Maximum results
        """
        try:
            # Refresh view
            self._register_parquet_view()

            # Escape search term to prevent SQL injection
            # Replace single quotes with double single quotes
            escaped_term = search_term.replace("'", "''")

            if column:
                # Search specific column - use parameterized approach
                query = f"""
                    SELECT * FROM all_records
                    WHERE CAST({column} AS VARCHAR) ILIKE '%{escaped_term}%'
                    LIMIT {limit}
                """
            else:
                # Get all columns and search across them
                columns_query = "DESCRIBE all_records"
                columns_df = self.connection.execute(columns_query).fetchdf()

                # Filter for text-like columns (VARCHAR, TEXT, or any string type)
                text_columns = []
                for idx, row in columns_df.iterrows():
                    col_type = str(row['column_type']).upper()
                    if any(t in col_type for t in ['VARCHAR', 'TEXT', 'STRING', 'CHAR']):
                        text_columns.append(row['column_name'])

                if not text_columns:
                    # If no text columns found, search all columns by casting
                    text_columns = columns_df['column_name'].tolist()

                # Build search conditions for each column
                where_clauses = [
                    f"CAST({col} AS VARCHAR) ILIKE '%{escaped_term}%'"
                    for col in text_columns
                ]
                where_condition = " OR ".join(where_clauses)

                query = f"""
                    SELECT * FROM all_records
                    WHERE {where_condition}
                    LIMIT {limit}
                """

            # Don't call execute_sql to avoid double view refresh
            start_time = datetime.now()
            result = self.connection.execute(query).fetchdf()
            duration = (datetime.now() - start_time).total_seconds()

            return {
                "status": "success",
                "data": result.to_dict(orient='records'),
                "row_count": len(result),
                "columns": list(result.columns),
                "duration_seconds": round(duration, 3),
                "query": query
            }

        except Exception as e:
            logger.error(f"❌ Search failed: {e}")
            return {
                "status": "error",
                "message": str(e)
            }

    def aggregate(
        self,
        group_by: str,
        agg_function: str = "COUNT",
        agg_column: str = "*"
    ) -> Dict[str, Any]:
        """
        Perform aggregation query

        Args:
            group_by: Column to group by
            agg_function: Aggregation function (COUNT, SUM, AVG, etc.)
            agg_column: Column to aggregate
        """
        query = f"""
            SELECT
                {group_by},
                {agg_function}({agg_column}) as result
            FROM all_records
            GROUP BY {group_by}
            ORDER BY result DESC
            LIMIT 100
        """
        return self.execute_sql(query)

    def close(self):
        """Close database connection"""
        if self.connection:
            self.connection.close()
            logger.info("🔌 DuckDB connection closed")


# Singleton instance
query_engine = DuckDBQueryEngine()
