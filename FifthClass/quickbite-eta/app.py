from pathlib import Path
from typing import Literal

import joblib
import pandas as pd
from fastapi import FastAPI
from pydantic import BaseModel, Field


MODEL_PATH = Path(__file__).resolve().parent / "eta_model.pkl"
FEATURES = [
    "distance_km",
    "prep_time_min",
    "rider_available",
    "is_raining",
]

app = FastAPI(title="QuickBite ETA")
model = joblib.load(MODEL_PATH)


class Order(BaseModel):
    distance_km: float = Field(gt=0, le=100)
    prep_time_min: float = Field(gt=0, le=240)
    rider_available: Literal[0, 1]
    is_raining: Literal[0, 1]


@app.get("/")
def health():
    return {"status": "QuickBite ETA is live"}


@app.post("/predict")
def predict(order: Order):
    features = pd.DataFrame([order.model_dump()], columns=FEATURES)
    eta_minutes = round(float(model.predict(features)[0]), 1)
    return {
        "eta_minutes": eta_minutes,
        "message": f"Your food arrives in {eta_minutes} minutes",
    }