from dotenv import load_dotenv
import os
from sqlalchemy import create_engine, text

load_dotenv()
db_url = os.getenv("DATABASE_URL")
print("Using DATABASE_URL:", db_url[:80] + "..." if db_url else "NOT SET")
engine = create_engine(db_url, pool_pre_ping=True, pool_size=5, max_overflow=2, connect_args={"sslmode":"require"})

with engine.connect() as conn:
    print(conn.execute(text("SELECT 1")).scalar())
