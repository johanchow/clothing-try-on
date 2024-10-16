import os
from mysql.connector import pooling
from contextlib import contextmanager

dbconfig = {
    "host": os.getenv("DB_HOST"),
    "port": os.getenv("DB_PORT"),
    "user": os.getenv("DB_USER"),
    "passwd": os.getenv("DB_PASSWORD"),
    "database": os.getenv("DB_DATABASE"),
}

pool = pooling.MySQLConnectionPool(
    pool_name = "clothing-try-on",
    pool_reset_session = False,
    pool_size = 30,
    **dbconfig
)

@contextmanager
def execute_sql():
    try:
        connection = pool.get_connection()
        cursor = connection.cursor(dictionary=True)
        yield cursor
    finally:
        connection.commit()
        connection.close()
