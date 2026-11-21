"""Load the clean CSVs into a SQLite database, one table per file."""
import sqlite3

import pandas as pd

TABLES = ["countries", "travellers", "trips", "incidents"]

with sqlite3.connect("data/travel_risk.db") as conn:
    for table in TABLES:
        df = pd.read_csv(f"data/clean/{table}.csv")
        df.to_sql(table, conn, if_exists="replace", index=False)
        count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        print(f"{table:12} {count} rows")
print("Loaded into data/travel_risk.db")