import os
import pyodbc
from dotenv import load_dotenv

load_dotenv()

def get_conn():
    server = os.getenv("MSSQL_SERVER", "localhost")
    port = os.getenv("MSSQL_PORT", "1433")
    user = os.getenv("MSSQL_USER", "sa")
    password = os.getenv("MSSQL_PASSWORD")
    database = os.getenv("MSSQL_DB", "ShopStream")

    conn_str = (
        "DRIVER={ODBC Driver 17 for SQL Server};"
        f"SERVER={server},{port};"
        f"DATABASE={database};"
        f"UID={user};PWD={password};"
        "TrustServerCertificate=yes;"
    )
    return pyodbc.connect(conn_str)
