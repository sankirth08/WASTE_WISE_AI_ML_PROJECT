from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, Query

from app.dependencies import get_current_user


router = APIRouter(prefix="/analytics", tags=["analytics"])
ROOT_DIR = Path(__file__).resolve().parents[4]
ML_DIR = ROOT_DIR / "ml"
RAW_DIR = ML_DIR / "data" / "raw"
ARTIFACT_DIR = ML_DIR / "artifacts"


def load_artifact(name: str) -> dict[str, Any]:
    path = ARTIFACT_DIR / name
    if not path.exists():
        raise HTTPException(status_code=503, detail=f"Model artifact is unavailable: {name}")
    return joblib.load(path)


def artifact_features(artifact: dict[str, Any]) -> list[str]:
    features = artifact.get("feature_columns", artifact.get("features"))
    if not features:
        raise HTTPException(status_code=503, detail="Model artifact does not declare input features")
    return list(features)


def calendar_features(frame: pd.DataFrame) -> pd.DataFrame:
    result = frame.copy()
    date = result["date"]
    result["calendar_year"] = date.dt.year
    result["calendar_month"] = date.dt.month
    result["calendar_day_of_week"] = date.dt.dayofweek
    result["calendar_day_of_year"] = date.dt.dayofyear
    result["calendar_week_of_year"] = date.dt.isocalendar().week.astype(int)
    result["calendar_is_weekend"] = (date.dt.dayofweek >= 5).astype(int)
    result["calendar_weekday_sin"] = np.sin(2 * np.pi * date.dt.dayofweek / 7)
    result["calendar_weekday_cos"] = np.cos(2 * np.pi * date.dt.dayofweek / 7)
    result["calendar_year_day_sin"] = np.sin(2 * np.pi * date.dt.dayofyear / 365.25)
    result["calendar_year_day_cos"] = np.cos(2 * np.pi * date.dt.dayofyear / 365.25)
    result["calendar_days_from_start"] = (date - date.min()).dt.days
    return result


def forecast_rows() -> pd.DataFrame:
    frame = pd.read_csv(RAW_DIR / "perishable_inventory.csv", parse_dates=["date"])
    frame["product_id"] = frame["product_id"].astype(str)
    frame = frame.sort_values(["product_id", "date"]).reset_index(drop=True)
    grouped_sales = frame.groupby("product_id", sort=False)["units_sold"]
    grouped_dates = frame.groupby("product_id", sort=False)["date"]
    frame["sales_lag_1d"] = grouped_sales.shift(1)
    frame["sales_lag_7d"] = grouped_sales.shift(7)
    frame["sales_mean_previous_7d"] = grouped_sales.transform(
        lambda values: values.shift(1).rolling(7, min_periods=7).mean()
    )
    frame["previous_date_1d"] = grouped_dates.shift(1)
    frame["previous_date_7d"] = grouped_dates.shift(7)
    frame.loc[(frame["date"] - frame["previous_date_1d"]).dt.days != 1, "sales_lag_1d"] = np.nan
    invalid_week = (frame["date"] - frame["previous_date_7d"]).dt.days != 7
    frame.loc[invalid_week, ["sales_lag_7d", "sales_mean_previous_7d"]] = np.nan
    frame = calendar_features(frame)
    return frame.dropna(subset=["sales_lag_1d", "sales_lag_7d", "sales_mean_previous_7d"])


@router.get("/dashboard")
def dashboard(
    days: int = Query(default=7, ge=7, le=30),
    _: dict[str, object] = Depends(get_current_user),
) -> dict[str, Any]:
    sales = pd.read_csv(RAW_DIR / "perishable_inventory.csv", parse_dates=["date"])
    batches = pd.read_csv(RAW_DIR / "inventory_batches.csv")
    waste = pd.read_csv(RAW_DIR / "perishable_inventory.csv")
    metrics = json.loads((ARTIFACT_DIR / "metrics.json").read_text(encoding="utf-8"))
    latest_date = sales["date"].max()
    start_date = latest_date - pd.Timedelta(days=days - 1)
    recent_sales = sales[sales["date"] >= start_date]
    return {
        "as_of": sales["date"].max().strftime("%Y-%m-%d"),
        "period_days": days,
        "products": int(sales["product_id"].nunique()),
        "units_sold": int(recent_sales["units_sold"].sum()),
        "waste_units": int(recent_sales["waste_units"].sum()),
        "batches_at_risk": int(batches["expiry_risk_label"].sum()),
        "metrics": metrics,
    }


@router.get("/forecast")
def forecast(_: dict[str, object] = Depends(get_current_user)) -> dict[str, Any]:
    artifact = load_artifact("demand_forecast.joblib")
    frame = forecast_rows()
    latest = frame.sort_values("date").groupby("product_id", as_index=False).tail(1).copy()
    latest["predicted_units"] = np.maximum(0, artifact["model"].predict(latest[artifact["feature_columns"]]))
    return {
        "model_metrics": artifact["metrics"],
        "items": latest[["product_id", "category", "date", "predicted_units"]].to_dict("records"),
    }


@router.get("/expiry-risk")
def expiry_risk(_: dict[str, object] = Depends(get_current_user)) -> dict[str, Any]:
    artifact = load_artifact("expiry_risk.joblib")
    frame = pd.read_csv(RAW_DIR / "inventory_batches.csv")
    frame["product_id"] = frame["product_id"].astype(str)
    features = frame[artifact_features(artifact)]
    frame["risk_probability"] = artifact["model"].predict_proba(features)[:, 1]
    frame["risk_label"] = (frame["risk_probability"] >= 0.5).astype(int)
    items = frame.sort_values("risk_probability", ascending=False).head(20)
    return {
        "model_metrics": artifact["metrics"],
        "items": items[["batch_id", "product_id", "category", "days_to_expiry", "quantity_remaining", "risk_probability", "risk_label"]].to_dict("records"),
    }


@router.get("/waste")
def waste(_: dict[str, object] = Depends(get_current_user)) -> dict[str, Any]:
    artifact = load_artifact("food_waste.joblib")
    frame = pd.read_csv(RAW_DIR / "perishable_inventory.csv", parse_dates=["date"])
    frame["product_id"] = frame["product_id"].astype(str)
    frame = frame.sort_values(["product_id", "date"]).reset_index(drop=True)
    grouped = frame.groupby("product_id", sort=False)
    frame["previous_date"] = grouped["date"].shift(1)
    for field in ["opening_stock", "units_received", "units_sold", "unit_price", "discount_pct", "days_to_expiry", "temperature_c", "stockout_flag"]:
        frame[f"previous_day_{field}"] = grouped[field].shift(1)
    frame = frame.loc[(frame["date"] - frame["previous_date"]).dt.days == 1].copy()
    frame = calendar_features(frame)
    latest = frame.sort_values("date").groupby("product_id", as_index=False).tail(1).copy()
    latest["predicted_waste_units"] = np.maximum(0, artifact["model"].predict(latest[artifact["feature_columns"]]))
    return {
        "model_metrics": artifact["metrics"],
        "items": latest[["product_id", "category", "date", "predicted_waste_units"]].to_dict("records"),
    }


@router.get("/discount-recommendations")
def discount_recommendations(_: dict[str, object] = Depends(get_current_user)) -> dict[str, Any]:
    artifact = load_artifact("discount_recommendation_prototype.joblib")
    recommendations = pd.read_csv(ARTIFACT_DIR / "discount_recommendations_prototype.csv")
    return {
        "model_metrics": artifact["metrics"],
        "prototype_warning": artifact["note"],
        "items": recommendations.head(50).to_dict("records"),
    }