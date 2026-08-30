import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv(override=True)

# Make sure this matches how you connect to Postgres in your app
DB_URL = os.getenv("DATABASE_URL", "postgresql+psycopg://postgres:admin@localhost/dbname")

engine = create_engine(DB_URL)

with engine.connect() as conn:
    print("Dropping old memories table...")
    # Cascade ensures dependent indexes are also dropped
    conn.execute(text("DROP TABLE IF EXISTS memories CASCADE;"))
    conn.commit()
    print("✅ Table dropped successfully! Your app will recreate it on the next run.")