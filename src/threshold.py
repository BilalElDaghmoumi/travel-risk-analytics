"""Phase 2: tune the decision threshold to catch more escalations."""
import sqlite3

import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import precision_score, recall_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

FEATURES_SQL = """
SELECT i.incident_id, i.severity, i.incident_type, i.incident_hour,
       c.region, c.risk_level, i.escalated,
       COUNT(DISTINCT t.traveller_id) AS travellers_exposed
FROM incidents i
JOIN countries c ON c.country = i.country
LEFT JOIN trips t
  ON t.country = i.country
 AND i.incident_date BETWEEN t.start_date AND t.end_date
GROUP BY i.incident_id
"""
with sqlite3.connect("data/travel_risk.db") as conn:
    df = pd.read_sql(FEATURES_SQL, conn)
df["is_night"] = (df["incident_hour"] < 6).astype(int)

NUMERIC = ["severity", "risk_level", "travellers_exposed", "is_night"]
CATEGORICAL = ["incident_type", "region"]
X, y = df[NUMERIC + CATEGORICAL], df["escalated"]
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.25, random_state=42, stratify=y
)

pipe = Pipeline([
    ("prep", ColumnTransformer([
        ("num", StandardScaler(), NUMERIC),
        ("cat", OneHotEncoder(handle_unknown="ignore"), CATEGORICAL),
    ])),
    ("model", LogisticRegression(max_iter=1000)),
])
pipe.fit(X_train, y_train)

# Probability of escalation for each test incident (0 to 1)
proba = pipe.predict_proba(X_test)[:, 1]

rows = []
for threshold in [0.5, 0.4, 0.3, 0.2]:
    pred = (proba >= threshold).astype(int)
    rows.append({
        "threshold": threshold,
        "flagged": int(pred.sum()),
        "escalations_caught": int(((pred == 1) & (y_test == 1)).sum()),
        "escalations_missed": int(((pred == 0) & (y_test == 1)).sum()),
        "false_alarms": int(((pred == 1) & (y_test == 0)).sum()),
        "recall": round(recall_score(y_test, pred), 2),
        "precision": round(precision_score(y_test, pred), 2),
    })
print(f"Test set: {len(y_test)} incidents, {int(y_test.sum())} actually escalated\n")
print(pd.DataFrame(rows).to_string(index=False))