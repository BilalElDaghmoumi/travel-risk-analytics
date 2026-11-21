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
# City coordinates (latitude, longitude) so Tableau doesn't have to guess
# ambiguous names like Houston. Lookups only - no randomness involved.
CITY_COORDS = {
    "Paris": (48.8566, 2.3522), "Lyon": (45.7640, 4.8357), "Marseille": (43.2965, 5.3698),
    "Berlin": (52.5200, 13.4050), "Munich": (48.1351, 11.5820), "Frankfurt": (50.1109, 8.6821),
    "Madrid": (40.4168, -3.7038), "Barcelona": (41.3874, 2.1686), "Valencia": (39.4699, -0.3763),
    "Istanbul": (41.0082, 28.9784), "Ankara": (39.9334, 32.8597), "Izmir": (38.4237, 27.1428),
    "New York": (40.7128, -74.0060), "Houston": (29.7604, -95.3698), "Chicago": (41.8781, -87.6298),
    "Mexico City": (19.4326, -99.1332), "Monterrey": (25.6866, -100.3161), "Guadalajara": (20.6597, -103.3496),
    "Sao Paulo": (-23.5505, -46.6333), "Rio de Janeiro": (-22.9068, -43.1729), "Brasilia": (-15.7975, -47.8919),
    "Bogota": (4.7110, -74.0721), "Medellin": (6.2442, -75.5812), "Cali": (3.4516, -76.5320),
    "Nairobi": (-1.2921, 36.8219), "Mombasa": (-4.0435, 39.6682), "Kisumu": (-0.0917, 34.7680),
    "Lagos": (6.5244, 3.3792), "Abuja": (9.0765, 7.3986), "Port Harcourt": (4.8156, 7.0498),
    "Johannesburg": (-26.2041, 28.0473), "Cape Town": (-33.9249, 18.4241), "Durban": (-29.8587, 31.0218),
    "Accra": (5.6037, -0.1870), "Kumasi": (6.6885, -1.6244), "Takoradi": (4.8845, -1.7554),
    "Cairo": (30.0444, 31.2357), "Alexandria": (31.2001, 29.9187), "Giza": (30.0131, 31.2089),
    "Amman": (31.9454, 35.9284), "Aqaba": (29.5321, 35.0063), "Irbid": (32.5556, 35.8500),
    "Dubai": (25.2048, 55.2708), "Abu Dhabi": (24.4539, 54.3773), "Sharjah": (25.3463, 55.4209),
    "Mumbai": (19.0760, 72.8777), "Delhi": (28.7041, 77.1025), "Bangalore": (12.9716, 77.5946),
    "Jakarta": (-6.2088, 106.8456), "Surabaya": (-7.2575, 112.7521), "Bali": (-8.6705, 115.2126),
    "Tokyo": (35.6762, 139.6503), "Osaka": (34.6937, 135.5023), "Yokohama": (35.4437, 139.6380),
    "Manila": (14.5995, 120.9842), "Cebu": (10.3157, 123.8854), "Davao": (7.1907, 125.4553),
    "Sydney": (-33.8688, 151.2093), "Melbourne": (-37.8136, 144.9631), "Perth": (-31.9505, 115.8605),
}
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
incidents.insert(3, "latitude", incidents["city"].map(lambda c: CITY_COORDS[c][0]))
incidents.insert(4, "longitude", incidents["city"].map(lambda c: CITY_COORDS[c][1]))

RAW.mkdir(parents=True, exist_ok=True)
for name, df in {"countries": countries, "travellers": travellers,
                 "trips": trips, "incidents": incidents}.items():
    df.to_csv(RAW / f"{name}.csv", index=False)
    print(f"{name}: {len(df)} rows")