import psycopg2
from dotenv import load_dotenv
import os

load_dotenv()

connection = psycopg2.connect(
    user=os.getenv("SUPABASE_DB_USER"),
    password=os.getenv("SUPABASE_DB_PASSWORD"),
    host=os.getenv("SUPABASE_DB_HOST"),
    port=os.getenv("SUPABASE_DB_PORT"),
    dbname=os.getenv("SUPABASE_DB_NAME"),
)

cursor = connection.cursor()

# INSERT simples
cursor.execute(
    """
    insert into public.test_logs (message)
    values (%s)
    returning id, created_at;
    """,
    ("Hello Supabase from Python 🚀",)
)

result = cursor.fetchone()
connection.commit()

print("Inserted:", result)

cursor.close()
connection.close()
