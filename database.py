import os
import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv
from contextlib import contextmanager

load_dotenv()

def get_db_connection():
    try:
        connection = mysql.connector.connect(
            host=os.getenv("MYSQL_HOST", "127.0.0.1"),
            port=int(os.getenv("MYSQL_PORT", "3306")),
            user=os.getenv("MYSQL_USER"),
            password=os.getenv("MYSQL_PASSWORD"),
            database=os.getenv("MYSQL_DB"),
            autocommit=False,
            use_pure=True
        )
        return connection
    except Error as e:
        print("Error while connecting to database:", e)
        raise

@contextmanager
def get_db_cursor():
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    try:
        yield cursor
        connection.commit()
    except Exception as e:
        connection.rollback()
        print("Error during DB operation:", e)
        raise
    finally:
        cursor.close()
        connection.close()