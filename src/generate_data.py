"""Generate fictional, slightly messy travel risk data: travellers, trips and incidents."""
import math
import random
from datetime import date, timedelta
from pathlib import Path

import pandas as pd

RAW = Path("data/raw")
random.seed(7)  # same "random" data every run

START, END = date(2025, 1, 1), date(2026, 6, 30)
DAYS = (END - START).days

# Fictional risk levels (1 = low, 5 = extreme) - for practice only
COUNTRIES = {
    "France": ("Europe", 1), "Germany": ("Europe", 1), "Spain": ("Europe", 1),
    "Turkey": ("Europe", 3), "United States": ("Americas", 2),
    "Mexico": ("Americas", 3), "Brazil": ("Americas", 3), "Colombia": ("Americas", 4),
    "Kenya": ("Africa", 3), "Nigeria": ("Africa", 4), "South Africa": ("Africa", 3),
    "Ghana": ("Africa", 2), "Egypt": ("Middle East", 3), "Jordan": ("Middle East", 2),
    "UAE": ("Middle East", 1), "India": ("Asia", 3), "Indonesia": ("Asia", 3),
    "Japan": ("Asia", 1), "Philippines": ("Asia", 4), "Australia": ("Oceania", 1),
}
INCIDENT_TYPES = {  # type: how much it pushes escalation up
    "Crime": 0.0, "Transport Disruption": -0.5, "Natural Disaster": 1.0,
    "Civil Unrest": 0.8, "Health Outbreak": 0.5, "Terrorism": 1.5,
}
DEPARTMENTS = ["Engineering", "Sales", "Operations", "Finance", "HR", "Logistics"]
OFFICES = ["London", "Manchester", "Dubai", "Singapore", "New York"]
# Main cities per country (cities are picked with a separate random generator,
# so adding them doesn't change any of the other generated values)
CITIES = {
    "France": ["Paris", "Lyon", "Marseille"], "Germany": ["Berlin", "Munich", "Frankfurt"],
    "Spain": ["Madrid", "Barcelona", "Valencia"], "Turkey": ["Istanbul", "Ankara", "Izmir"],
    "United States": ["New York", "Houston", "Chicago"], "Mexico": ["Mexico City", "Monterrey", "Guadalajara"],
    "Brazil": ["Sao Paulo", "Rio de Janeiro", "Brasilia"], "Colombia": ["Bogota", "Medellin", "Cali"],
    "Kenya": ["Nairobi", "Mombasa", "Kisumu"], "Nigeria": ["Lagos", "Abuja", "Port Harcourt"],
    "South Africa": ["Johannesburg", "Cape Town", "Durban"], "Ghana": ["Accra", "Kumasi", "Takoradi"],
    "Egypt": ["Cairo", "Alexandria", "Giza"], "Jordan": ["Amman", "Aqaba", "Irbid"],
    "UAE": ["Dubai", "Abu Dhabi", "Sharjah"], "India": ["Mumbai", "Delhi", "Bangalore"],
    "Indonesia": ["Jakarta", "Surabaya", "Bali"], "Japan": ["Tokyo", "Osaka", "Yokohama"],
    "Philippines": ["Manila", "Cebu", "Davao"], "Australia": ["Sydney", "Melbourne", "Perth"],
}
city_rng = random.Random(99)
CANONICAL = {c.lower(): c for c in CITIES}  # " kenya " -> "Kenya"
# Fictional client organisations - invented names, not real companies
CLIENTS = ["Acme Logistics", "Bluepeak Mining", "Harbourline Engineering",
           "Northstar Energy", "Silverleaf Consulting"]


def rand_date():
    return START + timedelta(days=random.randint(0, DAYS))


def messy_country(name):
    """Real exports are inconsistent: random casing and stray spaces."""
    r = random.random()
    if r < 0.05:
        return name.upper()
    if r < 0.10:
        return f" {name.lower()} "
    return name


# 1. Countries (clean reference table)
countries = pd.DataFrame(
    [(c, reg, risk) for c, (reg, risk) in COUNTRIES.items()],
    columns=["country", "region", "risk_level"],
)

# 2. Travellers
travellers = pd.DataFrame([{
    "traveller_id": f"T{i:04d}",
    "client": random.choice(CLIENTS),
    "department": random.choice(DEPARTMENTS),
    "home_office": random.choice(OFFICES),
} for i in range(1, 301)])

# 3. Trips (higher-risk countries get fewer visits)
names = list(COUNTRIES)
weights = [6 - COUNTRIES[c][1] for c in names]
trips = []
for i in range(1, 2001):
    start = rand_date()
    end = start + timedelta(days=random.randint(1, 14))
    if random.random() < 0.01:
        start, end = end, start  # data entry error: end before start
    trips.append({
        "trip_id": f"TR{i:05d}",
        "traveller_id": random.choice(travellers["traveller_id"]),
        "country": messy_country(random.choices(names, weights)[0]),
        "start_date": start.isoformat(),
        "end_date": end.isoformat(),
    })
trips += random.sample(trips, 30)  # duplicate rows from a double export
random.shuffle(trips)
trips = pd.DataFrame(trips)

trip_city = {tid: city_rng.choice(CITIES[CANONICAL[c.strip().lower()]])
             for tid, c in zip(trips["trip_id"], trips["country"])}  # duplicates share a city
trips.insert(3, "city", trips["trip_id"].map(trip_city))

# 4. Incidents (higher-risk countries get more incidents)
clean_trips = trips.drop_duplicates("trip_id").assign(c=lambda d: d["country"].str.strip().str.title())
incidents = []
for i in range(1, 601):
    country = random.choices(names, [COUNTRIES[c][1] ** 2 for c in names])[0]
    risk = COUNTRIES[country][1]
    itype = random.choice(list(INCIDENT_TYPES))
    severity = min(5, max(1, round(random.gauss(risk, 1))))
    day = rand_date()
    hour = random.randint(0, 23)
    on_site = clean_trips[(clean_trips["c"].str.lower() == country.lower())
                          & (clean_trips["start_date"] <= day.isoformat())
                          & (clean_trips["end_date"] >= day.isoformat())]
    exposed = len(on_site)
    # Escalation is more likely for severe incidents, serious types,
    # exposed travellers and night-time events (signal for Phase 2)
    score = -4 + 0.9 * severity + INCIDENT_TYPES[itype] + 0.6 * exposed + (0.5 if hour < 6 else 0)
    escalated = random.random() < 1 / (1 + math.exp(-score))
    incidents.append({
        "incident_id": f"INC{i:04d}",
        "country": messy_country(country),
        "incident_date": day.isoformat(),
        "incident_hour": hour,
        "incident_type": itype,
        "severity": severity,
        "escalated": "Yes" if escalated else "No",
    })
incidents = pd.DataFrame(incidents)
incidents.insert(2, "city", [city_rng.choice(CITIES[CANONICAL[c.strip().lower()]])
                             for c in incidents["country"]])

RAW.mkdir(parents=True, exist_ok=True)
for name, df in {"countries": countries, "travellers": travellers,
                 "trips": trips, "incidents": incidents}.items():
    df.to_csv(RAW / f"{name}.csv", index=False)
    print(f"{name}: {len(df)} rows")