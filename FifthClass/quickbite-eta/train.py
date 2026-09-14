from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor


MODEL_PATH = Path(__file__).resolve().parent / "eta_model.pkl"
FEATURES = [
    "distance_km",
    "prep_time_min",
    "rider_available",
    "is_raining",
]

np.random.seed(42)
n_samples = 5_000
df = pd.DataFrame(
    {
        "distance_km": np.random.uniform(0.5, 12, n_samples),
        "prep_time_min": np.random.uniform(5, 30, n_samples),
        "rider_available": np.random.randint(0, 2, n_samples),
        "is_raining": np.random.randint(0, 2, n_samples),
    }
)

df["eta_min"] = (
    8
    + df["distance_km"] * 3
    + df["prep_time_min"] * 0.7
    + df["is_raining"] * 9
    + (1 - df["rider_available"]) * 6
    + np.random.normal(0, 2, n_samples)
)

model = RandomForestRegressor(n_estimators=60, random_state=42)
model.fit(df[FEATURES], df["eta_min"])
joblib.dump(model, MODEL_PATH)
print(f"Model saved: {MODEL_PATH}")