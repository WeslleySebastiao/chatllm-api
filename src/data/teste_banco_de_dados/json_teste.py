import psycopg2
from dotenv import load_dotenv
import os
import json

load_dotenv()

connection = psycopg2.connect(
    user=os.getenv("SUPABASE_DB_USER"),
    password=os.getenv("SUPABASE_DB_PASSWORD"),
    host=os.getenv("SUPABASE_DB_HOST"),
    port=os.getenv("SUPABASE_DB_PORT"),
    dbname=os.getenv("SUPABASE_DB_NAME"),
)

cursor = connection.cursor()

cursor.execute(
    """
    insert into public.test_json (payload)
    values (%s)
    returning id;
    """,
    (json.dumps({
        "type": "agent_event",
        "agent": "planner",
        "content": "Decidir próximos passos",
        "confidence": 0.92
    }),)
)

print(cursor.fetchone())
connection.commit()
