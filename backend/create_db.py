import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

try:
    conn = psycopg2.connect(dbname='postgres', user='ishankumar', host='localhost', port=5432)
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cursor = conn.cursor()
    cursor.execute('CREATE DATABASE chatbot')
    print("Database 'chatbot' created successfully.")
    cursor.close()
    conn.close()
except Exception as e:
    print(f"Error creating database: {e}")
