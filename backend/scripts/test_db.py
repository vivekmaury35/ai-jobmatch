import sys
import os
import psycopg2

print("Attempting to connect to PostgreSQL...")
try:
    # Try with a 3-second connect timeout
    conn = psycopg2.connect("postgresql://jobmatch:password123@localhost:5432/jobmatch_db", connect_timeout=3)
    print("SUCCESS! Connected to database.")
    conn.close()
except Exception as e:
    print(f"FAILED to connect:")
    print(e)
