#!/usr/bin/env python3
"""
Inspect Neon database schema – list tables, columns, data types and constraints.
Usage:
  python tests/manual/inspect_schema.py
"""
from dotenv import load_dotenv
import os
from sqlalchemy import create_engine, inspect

load_dotenv()
db_url = os.getenv("DATABASE_URL")
if not db_url:
    print("ERROR: DATABASE_URL not set in .env")
    exit(1)

print("Connecting to Neon database...")
engine = create_engine(db_url, pool_pre_ping=True, pool_size=5, max_overflow=2, connect_args={"sslmode":"require"})

inspector = inspect(engine)
tables = inspector.get_table_names()

if not tables:
    print("No tables found in database.")
    exit(0)

print(f"\n{'='*80}")
print(f"NEON DATABASE SCHEMA – {len(tables)} table(s)")
print(f"{'='*80}\n")

for table_name in tables:
    print(f"\n📋 TABLE: {table_name}")
    print("-" * 80)
    
    columns = inspector.get_columns(table_name)
    pk = inspector.get_pk_constraint(table_name)
    fk = inspector.get_foreign_keys(table_name)
    indexes = inspector.get_indexes(table_name)
    
    # Columns
    print(f"  Columns ({len(columns)}):")
    for col in columns:
        nullable = "NULL" if col['nullable'] else "NOT NULL"
        default = f" DEFAULT {col['default']}" if col['default'] else ""
        print(f"    • {col['name']:25} {str(col['type']):20} {nullable}{default}")
    
    # Primary Key
    if pk and pk.get('constrained_columns'):
        print(f"  Primary Key: {', '.join(pk['constrained_columns'])}")
    
    # Foreign Keys
    if fk:
        print(f"  Foreign Keys ({len(fk)}):")
        for fk_obj in fk:
            cols = ', '.join(fk_obj['constrained_columns'])
            ref_table = fk_obj['referred_table']
            ref_cols = ', '.join(fk_obj['referred_columns'])
            print(f"    • {cols} → {ref_table}({ref_cols})")
    
    # Indexes
    if indexes:
        print(f"  Indexes ({len(indexes)}):")
        for idx in indexes:
            if not idx['name'].startswith('pg_toast'):
                cols = ', '.join(idx['column_names'])
                unique = " [UNIQUE]" if idx['unique'] else ""
                print(f"    • {idx['name']}{unique} on ({cols})")

print(f"\n{'='*80}")
print("✅ Schema inspection complete.")
