import pyodbc
from contextlib import contextmanager
from app.config import settings

class Database:
    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        conn = pyodbc.connect(
            f'DRIVER={{ODBC Driver 17 for SQL Server}};'
            f'SERVER={settings.DB_SERVER};'
            f'DATABASE={settings.DB_NAME};'
            f'UID={settings.DB_USER};'
            f'PWD={settings.DB_PASSWORD}'
        )
        try:
            yield conn
        finally:
            conn.close()

db = Database()