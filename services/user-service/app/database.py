import pymssql
from contextlib import contextmanager
from app.config import settings

class Database:
    @contextmanager
    def get_connection(self):
        conn = pymssql.connect(
            server=settings.DB_SERVER,
            user=settings.DB_USER,
            password=settings.DB_PASSWORD,
            database=settings.DB_NAME
        )
        try:
            yield conn
        finally:
            conn.close()

db = Database()
