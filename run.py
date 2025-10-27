"""
Main entry point for DuckParqStream
Starts the API server and optionally opens the web interface
"""
import sys
import subprocess
import webbrowser
from pathlib import Path
import time
import argparse

# Add backend to path
backend_dir = Path(__file__).parent / 'backend'
sys.path.insert(0, str(backend_dir))

from config import API_HOST, API_PORT


def start_server(open_browser: bool = True):
    """Start the FastAPI server"""
    print("=" * 60)
    print("🦆 DuckParqStream - Local JSON Database")
    print("=" * 60)
    print(f"📍 API Server: http://{API_HOST}:{API_PORT}")
    print(f"📚 API Docs: http://{API_HOST}:{API_PORT}/docs")
    print(f"🌐 Web UI: http://{API_HOST}:{API_PORT}/ui")
    print("=" * 60)
    print("\nPress Ctrl+C to stop the server\n")

    # Open browser after a short delay
    if open_browser:
        def open_ui():
            time.sleep(2)
            ui_path = Path(__file__).parent / "frontend" / "index.html"
            webbrowser.open(f"file://{ui_path.absolute()}")

        import threading
        threading.Thread(target=open_ui, daemon=True).start()

    # Start server
    import uvicorn
    from api import app

    try:
        uvicorn.run(
            app,
            host=API_HOST,
            port=API_PORT,
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n\n✅ Server stopped")


def generate_test_data(record_type: str = 'user', count: int = 1000):
    """Generate test data"""
    from test_data_generator import TestDataGenerator
    from ingestion import ingestion_engine

    print(f"🔄 Generating {count} {record_type} records...")

    generator = TestDataGenerator()
    records = generator.generate_batch(record_type, count)

    print(f"💾 Ingesting records...")
    result = ingestion_engine.append_to_parquet(records)

    if result["status"] == "success":
        print(f"✅ Successfully ingested {result['records_processed']} records")
        print(f"📁 File: {result['file']}")
        print(f"💽 Size: {result['file_size_mb']} MB")
    else:
        print(f"❌ Error: {result.get('message', 'Unknown error')}")


def query_stats():
    """Display dataset statistics"""
    from query_engine import query_engine
    from ingestion import ingestion_engine

    print("\n📊 Dataset Statistics")
    print("=" * 60)

    # File statistics
    files = ingestion_engine.get_file_stats()
    print(f"\n📁 Parquet Files: {len(files)}")
    for file_info in files:
        print(f"  - {file_info['filename']}: {file_info['row_count']:,} rows, {file_info['file_size_mb']:.2f} MB")

    # Query statistics
    stats = query_engine.get_statistics()
    if stats["status"] == "success":
        query_stats = stats["statistics"]
        print(f"\n📈 Total Records: {query_stats.get('total_records', 0):,}")

        if query_stats.get('date_range'):
            dr = query_stats['date_range']
            print(f"📅 Date Range: {dr['earliest']} to {dr['latest']}")

        if query_stats.get('weekly_distribution'):
            print(f"\n📊 Weekly Distribution:")
            for week_data in query_stats['weekly_distribution'][:5]:
                print(f"  - {week_data['week']}: {week_data['count']:,} records")

    print("=" * 60)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='DuckParqStream - Local JSON Database')
    parser.add_argument(
        'command',
        nargs='?',
        choices=['start', 'generate', 'stats'],
        default='start',
        help='Command to execute'
    )
    parser.add_argument(
        '--no-browser',
        action='store_true',
        help='Do not open browser automatically'
    )
    parser.add_argument(
        '--type',
        choices=['user', 'transaction', 'event', 'product', 'sensor'],
        default='user',
        help='Type of test data to generate'
    )
    parser.add_argument(
        '--count',
        type=int,
        default=1000,
        help='Number of records to generate'
    )

    args = parser.parse_args()

    if args.command == 'start':
        start_server(open_browser=not args.no_browser)
    elif args.command == 'generate':
        generate_test_data(args.type, args.count)
    elif args.command == 'stats':
        query_stats()
