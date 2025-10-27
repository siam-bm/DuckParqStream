"""
Test data generator for DuckParqStream
Generates realistic JSON data for testing and benchmarking
"""
import random
import string
from datetime import datetime, timedelta
from typing import List, Dict, Any
import json
from pathlib import Path


class TestDataGenerator:
    """Generate realistic test data for various scenarios"""

    def __init__(self):
        self.first_names = [
            'James', 'Mary', 'John', 'Patricia', 'Robert', 'Jennifer',
            'Michael', 'Linda', 'William', 'Elizabeth', 'David', 'Susan'
        ]
        self.last_names = [
            'Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia',
            'Miller', 'Davis', 'Rodriguez', 'Martinez', 'Wilson', 'Anderson'
        ]
        self.statuses = ['active', 'pending', 'inactive', 'suspended']
        self.categories = ['electronics', 'clothing', 'food', 'books', 'sports', 'toys']
        self.countries = ['USA', 'UK', 'Canada', 'Germany', 'France', 'Japan', 'Australia']

    def generate_user_record(self, user_id: int) -> Dict[str, Any]:
        """Generate a single user record"""
        first_name = random.choice(self.first_names)
        last_name = random.choice(self.last_names)

        return {
            'id': f'user_{user_id}',
            'record_id': f'user_{user_id}',
            'first_name': first_name,
            'last_name': last_name,
            'email': f'{first_name.lower()}.{last_name.lower()}@example.com',
            'age': random.randint(18, 80),
            'country': random.choice(self.countries),
            'status': random.choice(self.statuses),
            'balance': round(random.uniform(0, 10000), 2),
            'created_at': (
                datetime.now() - timedelta(days=random.randint(0, 365))
            ).isoformat()
        }

    def generate_transaction_record(self, transaction_id: int) -> Dict[str, Any]:
        """Generate a single transaction record"""
        return {
            'id': f'txn_{transaction_id}',
            'record_id': f'txn_{transaction_id}',
            'user_id': f'user_{random.randint(1, 1000)}',
            'amount': round(random.uniform(1, 1000), 2),
            'currency': random.choice(['USD', 'EUR', 'GBP', 'JPY']),
            'category': random.choice(self.categories),
            'status': random.choice(['completed', 'pending', 'failed']),
            'timestamp': (
                datetime.now() - timedelta(hours=random.randint(0, 720))
            ).isoformat()
        }

    def generate_event_record(self, event_id: int) -> Dict[str, Any]:
        """Generate a single event/log record"""
        event_types = ['login', 'logout', 'purchase', 'view', 'click', 'error']
        severity_levels = ['info', 'warning', 'error', 'critical']

        return {
            'id': f'event_{event_id}',
            'record_id': f'event_{event_id}',
            'event_type': random.choice(event_types),
            'user_id': f'user_{random.randint(1, 1000)}',
            'severity': random.choice(severity_levels),
            'message': f'Event {event_id} occurred',
            'metadata': {
                'ip_address': f'{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}',
                'user_agent': 'Mozilla/5.0',
                'session_id': ''.join(random.choices(string.ascii_letters + string.digits, k=32))
            },
            'timestamp': (
                datetime.now() - timedelta(minutes=random.randint(0, 10080))
            ).isoformat()
        }

    def generate_product_record(self, product_id: int) -> Dict[str, Any]:
        """Generate a single product record"""
        return {
            'id': f'prod_{product_id}',
            'record_id': f'prod_{product_id}',
            'name': f'Product {product_id}',
            'category': random.choice(self.categories),
            'price': round(random.uniform(1, 500), 2),
            'stock': random.randint(0, 1000),
            'rating': round(random.uniform(1, 5), 1),
            'reviews_count': random.randint(0, 500),
            'is_available': random.choice([True, False]),
            'tags': random.sample(['new', 'sale', 'popular', 'limited', 'bestseller'], k=random.randint(0, 3)),
            'created_at': (
                datetime.now() - timedelta(days=random.randint(0, 730))
            ).isoformat()
        }

    def generate_sensor_data(self, sensor_id: int) -> Dict[str, Any]:
        """Generate IoT sensor data"""
        return {
            'id': f'sensor_{sensor_id}',
            'record_id': f'sensor_{sensor_id}',
            'sensor_id': f'SENSOR_{random.randint(1, 100):03d}',
            'temperature': round(random.uniform(-20, 50), 2),
            'humidity': round(random.uniform(0, 100), 2),
            'pressure': round(random.uniform(950, 1050), 2),
            'battery_level': round(random.uniform(0, 100), 1),
            'location': {
                'lat': round(random.uniform(-90, 90), 6),
                'lon': round(random.uniform(-180, 180), 6)
            },
            'status': random.choice(['online', 'offline', 'maintenance']),
            'timestamp': (
                datetime.now() - timedelta(seconds=random.randint(0, 3600))
            ).isoformat()
        }

    def generate_batch(
        self,
        record_type: str = 'user',
        count: int = 1000,
        start_id: int = 1
    ) -> List[Dict[str, Any]]:
        """
        Generate a batch of test records

        Args:
            record_type: Type of records to generate
                         (user, transaction, event, product, sensor)
            count: Number of records to generate
            start_id: Starting ID for records

        Returns:
            List of generated records
        """
        generators = {
            'user': self.generate_user_record,
            'transaction': self.generate_transaction_record,
            'event': self.generate_event_record,
            'product': self.generate_product_record,
            'sensor': self.generate_sensor_data
        }

        if record_type not in generators:
            raise ValueError(f"Unknown record type: {record_type}")

        generator = generators[record_type]
        return [generator(start_id + i) for i in range(count)]

    def save_to_file(
        self,
        records: List[Dict[str, Any]],
        filepath: Path,
        format: str = 'json'
    ):
        """
        Save generated records to file

        Args:
            records: List of records to save
            filepath: Output file path
            format: 'json' or 'jsonl'
        """
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)

        if format == 'json':
            with open(filepath, 'w') as f:
                json.dump(records, f, indent=2)
        elif format == 'jsonl':
            with open(filepath, 'w') as f:
                for record in records:
                    f.write(json.dumps(record) + '\n')
        else:
            raise ValueError(f"Unknown format: {format}")

    def generate_large_dataset(
        self,
        record_type: str,
        total_records: int,
        batch_size: int = 10000,
        output_dir: Path = None
    ):
        """
        Generate large dataset in batches and save to files

        Args:
            record_type: Type of records to generate
            total_records: Total number of records
            batch_size: Records per file
            output_dir: Directory to save files

        Returns:
            List of generated file paths
        """
        if output_dir is None:
            output_dir = Path('test_data')

        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        file_paths = []
        batches = (total_records + batch_size - 1) // batch_size

        for batch_num in range(batches):
            start_id = batch_num * batch_size + 1
            count = min(batch_size, total_records - batch_num * batch_size)

            records = self.generate_batch(record_type, count, start_id)

            filename = f'{record_type}_batch_{batch_num + 1}.json'
            filepath = output_dir / filename

            self.save_to_file(records, filepath, format='json')
            file_paths.append(filepath)

            print(f"Generated batch {batch_num + 1}/{batches}: {filepath} ({count} records)")

        return file_paths


# CLI interface
if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Generate test data for DuckParqStream')
    parser.add_argument(
        '--type',
        choices=['user', 'transaction', 'event', 'product', 'sensor'],
        default='user',
        help='Type of records to generate'
    )
    parser.add_argument(
        '--count',
        type=int,
        default=1000,
        help='Number of records to generate'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='test_data/sample.json',
        help='Output file path'
    )
    parser.add_argument(
        '--format',
        choices=['json', 'jsonl'],
        default='json',
        help='Output format'
    )
    parser.add_argument(
        '--batch-size',
        type=int,
        default=10000,
        help='Records per batch for large datasets'
    )

    args = parser.parse_args()

    generator = TestDataGenerator()

    if args.count <= args.batch_size:
        # Single file
        records = generator.generate_batch(args.type, args.count)
        generator.save_to_file(records, Path(args.output), args.format)
        print(f"✅ Generated {args.count} {args.type} records to {args.output}")
    else:
        # Multiple files
        output_dir = Path(args.output).parent
        file_paths = generator.generate_large_dataset(
            args.type,
            args.count,
            args.batch_size,
            output_dir
        )
        print(f"✅ Generated {args.count} records across {len(file_paths)} files")
