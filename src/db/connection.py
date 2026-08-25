import os
from contextlib import contextmanager
from typing import Any, Generator
import duckdb
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from src.config import settings
from src.observability.logger import logger


class DatabaseManager:
    """Manages database connections for PostGIS and DuckDB Spatial backends."""

    def __init__(self):
        self._engine: Engine | None = None
        self._duckdb_conn: duckdb.DuckDBPyConnection | None = None

    def get_postgres_engine(self) -> Engine:
        if self._engine is None:
            self._engine = create_engine(
                settings.postgres_uri,
                pool_size=5,
                max_overflow=10,
                pool_pre_ping=True,
            )
        return self._engine

    def get_duckdb_connection(self) -> duckdb.DuckDBPyConnection:
        if self._duckdb_conn is None:
            self._duckdb_conn = duckdb.connect(settings.DUCKDB_PATH)
            # Install and load spatial extension
            try:
                self._duckdb_conn.execute("INSTALL spatial; LOAD spatial;")
            except Exception as e:
                logger.warning(f"DuckDB spatial extension installation warning: {e}")
        return self._duckdb_conn

    def is_postgres_available(self) -> bool:
        try:
            engine = self.get_postgres_engine()
            with engine.connect() as conn:
                conn.execute("SELECT 1")
            return True
        except Exception:
            return False


db_manager = DatabaseManager()
