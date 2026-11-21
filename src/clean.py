"""Clean the raw travel risk data and run data quality checks."""
from pathlib import Path

import pandas as pd

RAW, CLEAN = Path("data/raw"), Path("data/clean")

countries = pd.read_csv(RAW / "countries.csv")
travellers = pd.read_csv(RAW / "travellers.csv")
trips = pd.read_csv(RAW / "trips.csv")
incidents = pd.read_csv(RAW / "incidents.csv")

# Lookup table: " kenya " / "KENYA" -> "Kenya" (matches the official spelling, e.g. "UAE")
COUNTRY_LOOKUP = {c.lower(): c for c in countries["country"]}


def standardise_country(series):
    return series.str.strip().str.lower().map(COUNTRY_LOOKUP)


# --- Trips ---
before = len(trips)
trips = trips.drop_duplicates(subset="trip_id")
duplicates_removed = before - len(trips)

trips["country"] = standardise_country(trips["country"])
trips["start_date"] = pd.to_datetime(trips["start_date"])
trips["end_date"] = pd.to_datetime(trips["end_date"])

# Fix trips entered back to front (end before start) by swapping the dates
reversed_mask = trips["end_date"] < trips["start_date"]
reversed_trips = int(reversed_mask.sum())
trips.loc[reversed_mask, ["start_date", "end_date"]] = (
    trips.loc[reversed_mask, ["end_date", "start_date"]].values
)
trips["trip_days"] = (trips["end_date"] - trips["start_date"]).dt.days

# --- Incidents ---
incidents["country"] = standardise_country(incidents["country"])
incidents["incident_date"] = pd.to_datetime(incidents["incident_date"])
incidents["escalated"] = incidents["escalated"].map({"Yes": 1, "No": 0})

# --- Data quality checks ---
checks = {
    "trip duplicates removed": duplicates_removed,
    "reversed trips fixed": reversed_trips,
    "trips": len(trips),
    "incidents": len(incidents),
    "unknown trip countries": int(trips["country"].isna().sum()),
    "unknown incident countries": int(incidents["country"].isna().sum()),
    "trips with unknown traveller": int((~trips["traveller_id"].isin(travellers["traveller_id"])).sum()),
    "trips ending before start": int((trips["end_date"] < trips["start_date"]).sum()),
    "severity outside 1-5": int((~incidents["severity"].between(1, 5)).sum()),
    "hour outside 0-23": int((~incidents["incident_hour"].between(0, 23)).sum()),
    "missing escalation flag": int(incidents["escalated"].isna().sum()),
}
for name, value in checks.items():
    print(f"{name:30} {value}")

assert checks["unknown trip countries"] == 0, "Trip country not in countries list"
assert checks["unknown incident countries"] == 0, "Incident country not in countries list"
assert checks["trips with unknown traveller"] == 0, "Trip points to a traveller that doesn't exist"
assert checks["trips ending before start"] == 0, "Some trips still end before they start"
assert checks["severity outside 1-5"] == 0, "Unexpected severity values"
assert checks["hour outside 0-23"] == 0, "Unexpected hour values"
assert checks["missing escalation flag"] == 0, "Escalated must be Yes or No"

# --- Save ---
CLEAN.mkdir(parents=True, exist_ok=True)
for name, df in {"countries": countries, "travellers": travellers,
                 "trips": trips, "incidents": incidents}.items():
    df.to_csv(CLEAN / f"{name}.csv", index=False)
print("\nAll checks passed. Clean files saved to data/clean/")