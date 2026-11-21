"""Export two flat, Tableau-ready CSVs from the SQLite database."""
import sqlite3

import pandas as pd

INCIDENTS_SQL = """
SELECT i.incident_id, i.country, c.region, c.risk_level,
       i.incident_date, i.incident_hour, i.incident_type, i.severity, i.escalated,
       COUNT(DISTINCT t.traveller_id) AS travellers_exposed
FROM incidents i
JOIN countries c ON c.country = i.country
LEFT JOIN trips t
  ON t.country = i.country
 AND i.incident_date BETWEEN t.start_date AND t.end_date
GROUP BY i.incident_id
"""

EXPOSURES_SQL = """
SELECT i.incident_id, i.country, c.region, i.incident_date, i.incident_type,
       i.severity, i.escalated, t.trip_id, tr.traveller_id, tr.client, tr.department
FROM incidents i
JOIN countries c ON c.country = i.country
JOIN trips t
  ON t.country = i.country
 AND i.incident_date BETWEEN t.start_date AND t.end_date
JOIN travellers tr ON tr.traveller_id = t.traveller_id
"""

with sqlite3.connect("data/travel_risk.db") as conn:
    for name, sql in {"tableau_incidents": INCIDENTS_SQL,
                      "tableau_exposures": EXPOSURES_SQL}.items():
        df = pd.read_sql(sql, conn)
        df.to_csv(f"data/clean/{name}.csv", index=False)
        print(f"{name}: {len(df)} rows")