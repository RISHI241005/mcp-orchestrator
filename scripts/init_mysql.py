"""Initialize MySQL database and create required tables for MCP Orchestrator.

Reads the following environment variables:
- ORCH_DB_HOST (default: localhost)
- ORCH_DB_PORT (default: 3306)
- ORCH_DB_USER
- ORCH_DB_PASS
- ORCH_DB_NAME (default: mcp_orchestrator)

This script will create the database (if missing) and the tables used by the app.
"""
import os
import sys

try:
    import pymysql
except Exception as exc:
    print("pymysql is required to run this script. Install it in your venv: pip install PyMySQL")
    raise

HOST = os.environ.get("ORCH_DB_HOST", "localhost")
PORT = int(os.environ.get("ORCH_DB_PORT", "3306"))
USER = os.environ.get("ORCH_DB_USER", "root")
PASS = os.environ.get("ORCH_DB_PASS", "")
DB = os.environ.get("ORCH_DB_NAME", "mcp_orchestrator")

print(f"Connecting to MySQL {HOST}:{PORT} as {USER} to create database {DB} (password not shown)")

# Connect to server (no db)
conn = pymysql.connect(host=HOST, port=PORT, user=USER, password=PASS, autocommit=True)
cur = conn.cursor()
cur.execute(f"CREATE DATABASE IF NOT EXISTS `{DB}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
print("Database ensured.")
cur.close()
conn.close()

# Connect to the created DB and create tables
conn = pymysql.connect(host=HOST, port=PORT, user=USER, password=PASS, database=DB, autocommit=True)
cur = conn.cursor()

# Create tasks table
cur.execute("""
CREATE TABLE IF NOT EXISTS tasks (
    id VARCHAR(255) PRIMARY KEY,
    payload LONGTEXT NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
""")
print("Created/ensured tasks table.")

# Create memory table
cur.execute("""
CREATE TABLE IF NOT EXISTS memory (
    `key` VARCHAR(191) PRIMARY KEY,
    `value` LONGTEXT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
""")
print("Created/ensured memory table.")

cur.close()
conn.close()
print("MySQL initialization complete.")
