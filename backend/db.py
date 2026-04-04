import psycopg2
import psycopg2.extras
from contextlib import contextmanager
import os

def _cfg():
    return {
        "host":     os.getenv("POSTGRES_HOST", "postgres"),
        "port":     int(os.getenv("POSTGRES_PORT", "5432")),
        "dbname":   os.getenv("POSTGRES_DB", "quasar"),
        "user":     os.getenv("POSTGRES_USER", "postgres"),
        "password": os.getenv("POSTGRES_PASSWORD", "postgres"),
    }

@contextmanager
def get_connection():
    conn = psycopg2.connect(**_cfg(), cursor_factory=psycopg2.extras.RealDictCursor)
    try:
        yield conn
    finally:
        conn.close()
