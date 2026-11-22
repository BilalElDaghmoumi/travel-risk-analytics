"""Phase 2: predict which incidents get escalated."""
import sqlite3

import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

# 1. Build one row per incident with its features (same exposure logic as the SQL)
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

df["is_night"] = (df["incident_hour"] < 6).astype(int)  # feature engineering

NUMERIC = ["severity", "risk_level", "travellers_exposed", "is_night"]
CATEGORICAL = ["incident_type", "region"]
X = df[NUMERIC + CATEGORICAL]
y = df["escalated"]

# 2. Hold back 25% of incidents the model never sees during training
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.25, random_state=42, stratify=y
)
print(f"Training on {len(X_train)} incidents, testing on {len(X_test)}")
print(f"Escalation rate in test set: {y_test.mean():.0%}\n")

# 3. Baseline: always guess the most common answer
baseline = max(y_test.mean(), 1 - y_test.mean())
print(f"Baseline accuracy (always guess the majority): {baseline:.0%}\n")

preprocess = ColumnTransformer([
    ("num", StandardScaler(), NUMERIC),
    ("cat", OneHotEncoder(handle_unknown="ignore"), CATEGORICAL),
])

models = {
    "Logistic regression": LogisticRegression(max_iter=1000),
    "Random forest": RandomForestClassifier(n_estimators=300, max_depth=5, random_state=42),
}

for name, model in models.items():
    pipe = Pipeline([("prep", preprocess), ("model", model)])
    pipe.fit(X_train, y_train)
    pred = pipe.predict(X_test)
    print(f"=== {name} ===")
    print(f"Accuracy: {accuracy_score(y_test, pred):.0%}")
    print("Confusion matrix (rows = actual, columns = predicted; 0 = not escalated, 1 = escalated):")
    print(confusion_matrix(y_test, pred))
    print(classification_report(y_test, pred, target_names=["not escalated", "escalated"], digits=2))

    if name == "Logistic regression":
        names = pipe.named_steps["prep"].get_feature_names_out()
        coefs = pd.Series(pipe.named_steps["model"].coef_[0], index=names).sort_values(ascending=False)
        print("What pushes escalation up (+) or down (-):")
        print(coefs.round(2).to_string(), "\n")
    else:
        names = pipe.named_steps["prep"].get_feature_names_out()
        imp = pd.Series(pipe.named_steps["model"].feature_importances_, index=names).sort_values(ascending=False)
        print("Feature importance:")
        print(imp.round(3).head(8).to_string(), "\n")