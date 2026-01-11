"""
Database Integration Tests
Actual database connections and transactions.
"""

import os
import sys
from pathlib import Path
from typing import Dict, Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

db_test_results: Dict[str, Any] = {
    "passed": 0,
    "failed": 0,
    "errors": [],
}


def test_database_connection():
    """Test database connection."""
    try:
        from backend.src.db.client import DatabaseClient
        from backend.src.config.base_settings import settings
        
        # Try to connect to database
        dsn = os.getenv("POSTGRES_DSN") or os.getenv("DATABASE_URL") or settings.postgres_dsn
        
        if not dsn or dsn == "postgresql://user:pass@localhost/dbname":
            db_test_results["errors"].append("Database DSN not configured, skipping connection test")
            return
        
        client = DatabaseClient(dsn)
        
        # Try to execute a simple query
        with client.connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
                result = cur.fetchone()
                assert result is not None
                assert result[0] == 1
        
        db_test_results["passed"] += 1
        print("  [PASS] Database connection successful")
        
    except Exception as e:
        db_test_results["failed"] += 1
        error_msg = f"Database connection failed: {str(e)[:200]}"
        db_test_results["errors"].append(error_msg)
        print(f"  [FAIL] {error_msg}")


def test_database_schema():
    """Test database schema existence."""
    try:
        from backend.src.db.client import DatabaseClient
        from backend.src.config.base_settings import settings
        
        dsn = os.getenv("POSTGRES_DSN") or os.getenv("DATABASE_URL") or settings.postgres_dsn
        
        if not dsn or dsn == "postgresql://user:pass@localhost/dbname":
            db_test_results["errors"].append("Database DSN not configured, skipping schema test")
            return
        
        client = DatabaseClient(dsn)
        
        # Check if required tables exist
        with client.connection() as conn:
            with conn.cursor() as cur:
                # Check for projects table
                cur.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_name = 'projects'
                    )
                """)
                projects_exists = cur.fetchone()[0]
                
                # Check for reports_history table
                cur.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_name = 'reports_history'
                    )
                """)
                reports_exists = cur.fetchone()[0]
                
                # At least one table should exist
                assert projects_exists or reports_exists, "No expected tables found in database"
        
        db_test_results["passed"] += 1
        print("  [PASS] Database schema check successful")
        
    except Exception as e:
        db_test_results["failed"] += 1
        error_msg = f"Database schema check failed: {str(e)[:200]}"
        db_test_results["errors"].append(error_msg)
        print(f"  [FAIL] {error_msg}")


def test_database_transaction():
    """Test database transaction validation."""
    try:
        from backend.src.db.client import DatabaseClient
        from backend.src.config.base_settings import settings
        
        dsn = os.getenv("POSTGRES_DSN") or os.getenv("DATABASE_URL") or settings.postgres_dsn
        
        if not dsn or dsn == "postgresql://user:pass@localhost/dbname":
            db_test_results["errors"].append("Database DSN not configured, skipping transaction test")
            return
        
        client = DatabaseClient(dsn)
        
        # Note: DatabaseClient uses autocommit=True, so transactions are handled differently
        # Test that invalid data is rejected (validation)
        with client.connection() as conn:
            try:
                with conn.cursor() as cur:
                    # Try to insert invalid data (will fail)
                    cur.execute("""
                        INSERT INTO projects (id, name, country, sector, created_at)
                        VALUES (NULL, 'Test', 'ITA', 'renewable', NOW())
                    """)
                # Should not reach here - should raise an error
                db_test_results["errors"].append("Expected validation error for NULL id, but insert succeeded")
                db_test_results["failed"] += 1
            except Exception as e:
                # Expected - database should reject NULL id
                if "NULL" in str(e) or "NOT NULL" in str(e) or "null value" in str(e).lower():
                    db_test_results["passed"] += 1
                    print("  [PASS] Database validation works (rejects NULL values)")
                else:
                    db_test_results["failed"] += 1
                    error_msg = f"Database transaction test failed: {str(e)[:200]}"
                    db_test_results["errors"].append(error_msg)
                    print(f"  [FAIL] {error_msg}")
        
    except Exception as e:
        db_test_results["failed"] += 1
        error_msg = f"Database transaction test failed: {str(e)[:200]}"
        db_test_results["errors"].append(error_msg)
        print(f"  [FAIL] {error_msg}")


def test_model_run_logging():
    """Test model run logging functionality."""
    try:
        from backend.src.db.model_runs import ModelRunLogger, ModelRunRecord
        import uuid
        from datetime import datetime, UTC
        
        # Test ModelRunRecord creation with correct fields
        record = ModelRunRecord(
            run_id=str(uuid.uuid4()),
            model_name="biodiversity",
            model_version="1.0.0",
            dataset_source="synthetic",
            candidate_models=["random_forest", "gradient_boosting"],
            selected_model="random_forest",
            metrics={"accuracy": 0.85, "f1": 0.82},
            created_at=datetime.now(UTC),
        )
        
        assert record.run_id is not None
        assert record.model_name == "biodiversity"
        assert record.model_version == "1.0.0"
        assert "metrics" in record.__dict__
        
        # Test as_db_tuple method
        db_tuple = record.as_db_tuple()
        assert len(db_tuple) == 9  # id, run_id, model_name, model_version, dataset_source, candidate_models, selected_model, metrics, created_at
        
        db_test_results["passed"] += 1
        print("  [PASS] Model run record creation works")
        
    except Exception as e:
        db_test_results["failed"] += 1
        error_msg = f"Model run logging test failed: {str(e)[:200]}"
        db_test_results["errors"].append(error_msg)
        print(f"  [FAIL] {error_msg}")


def main():
    """Run all database integration tests."""
    print("=" * 60)
    print("DATABASE INTEGRATION TESTS")
    print("=" * 60)
    print("Note: These tests require a running PostgreSQL database")
    print("=" * 60)
    
    test_database_connection()
    test_database_schema()
    test_database_transaction()
    test_model_run_logging()
    
    print("\n" + "=" * 60)
    print("DATABASE INTEGRATION TEST SUMMARY")
    print("=" * 60)
    print(f"Passed: {db_test_results['passed']}")
    print(f"Failed: {db_test_results['failed']}")
    if db_test_results["errors"]:
        print("\nErrors/Warnings:")
        for error in db_test_results["errors"][:5]:
            print(f"  - {error}")
    print("=" * 60)
    
    return 0 if db_test_results["failed"] == 0 else 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
