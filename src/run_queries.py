"""Run every query in sql/queries.sql and print the results."""
import sqlite3

import pandas as pd

with sqlite3.connect("data/travel_risk.db") as conn:
    queries = open("sql/queries.sql").read().split(";")
    for query in queries:
        if query.strip():
            title = query.strip().splitlines()[0]  # the "-- 1. ..." comment line
            print(title)
            print(pd.read_sql(query, conn).to_string(index=False), "\n")