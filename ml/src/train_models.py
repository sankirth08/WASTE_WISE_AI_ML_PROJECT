"""Train and evaluate the WasteWise forecasting and recommendation models."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    f1_score,
    mean_absolute_error,
    mean_squared_error,
    precision_score,
    r2_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import GroupShuffleSplit, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder


ML_DIR = Path(__file__).resolve().parents[1]
RAW_DIR = ML_DIR / "data" / "raw"
ARTIFACT_DIR = ML_DIR / "artifacts"
RANDOM_STATE = 42


def make_pipeline(model: Any, features: pd.DataFrame) -> Pipeline:
    categorical = features.select_dtypes(include=["object", "category"]).columns.tolist()
    numeric = [column for column in features.columns if column not in categorical]
    transformers: list[tuple[str, Pipeline, list[str]]] = []
    if numeric:
        transformers.append(
            ("numeric", Pipeline([("imputer", SimpleImputer(strategy="median"))]), numeric)
        )
    if categorical:
        transformers.append(
            (
                "categorical",
                Pipeline(
                    [
                        ("imputer", SimpleImputer(strategy="most_frequent")),
                        ("encoder", OneHotEncoder(handle_unknown="ignore")),
                    ]
                ),
                categorical,
            )
        )
    return Pipeline(
        [("preprocessor", ColumnTransformer(transformers)), ("model", model)]
    )


def add_calendar_features(frame: pd.DataFrame) -> pd.DataFrame:
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


def chronological_split(
    frame: pd.DataFrame, date_column: str = "date"
) -> tuple[pd.DataFrame, pd.DataFrame, str]:
    dates = pd.Index(frame[date_column].drop_duplicates().sort_values())
    split_index = int(len(dates) * 0.8)
    if split_index == 0 or split_index >= len(dates):
        raise ValueError("Not enough distinct dates for a chronological 80/20 split")
    cutoff = dates[split_index]
    train = frame[frame[date_column] < cutoff]
    test = frame[frame[date_column] >= cutoff]
    if train.empty or test.empty:
        raise ValueError("Chronological split produced an empty train or test set")
    return train, test, cutoff.strftime("%Y-%m-%d")


def regression_metrics(actual: pd.Series, predicted: np.ndarray) -> dict[str, float]:
    return {
        "mae": float(mean_absolute_error(actual, predicted)),
        "rmse": float(mean_squared_error(actual, predicted) ** 0.5),
        "r2": float(r2_score(actual, predicted)),
    }


def save_artifact(
    filename: str,
    model: Pipeline,
    features: list[str],
    target: str,
    metrics: dict[str, Any],
    note: str,
) -> None:
    joblib.dump(
        {
            "model": model,
            "feature_columns": features,
            "target": target,
            "metrics": metrics,
            "note": note,
        },
        ARTIFACT_DIR / filename,
    )


def train_demand_forecast(results: dict[str, Any]) -> None:
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
    frame = add_calendar_features(frame)

    features = [
        "product_id",
        "category",
        "calendar_year",
        "calendar_month",
        "calendar_day_of_week",
        "calendar_day_of_year",
        "calendar_week_of_year",
        "calendar_is_weekend",
        "calendar_weekday_sin",
        "calendar_weekday_cos",
        "calendar_year_day_sin",
        "calendar_year_day_cos",
        "calendar_days_from_start",
        "sales_lag_1d",
        "sales_lag_7d",
        "sales_mean_previous_7d",
        "unit_price",
        "discount_pct",
        "opening_stock",
        "units_received",
    ]
    frame = frame.dropna(subset=["sales_lag_1d", "sales_lag_7d", "sales_mean_previous_7d"])
    train, test, cutoff = chronological_split(frame)
    model = make_pipeline(
        RandomForestRegressor(
            n_estimators=300,
            min_samples_leaf=2,
            random_state=RANDOM_STATE,
            n_jobs=-1,
        ),
        train[features],
    )
    model.fit(train[features], train["units_sold"])
    predicted = model.predict(test[features])
    scores = regression_metrics(test["units_sold"], predicted)
    scores["lag_1d_baseline_mae"] = float(
        mean_absolute_error(test["units_sold"], test["sales_lag_1d"])
    )
    scores["train_rows"] = len(train)
    scores["test_rows"] = len(test)
    scores["test_start_date"] = cutoff
    scores["validation"] = "chronological rolling one-day-ahead; prices and promotions assumed known"
    final_model = make_pipeline(
        RandomForestRegressor(
            n_estimators=300,
            min_samples_leaf=2,
            random_state=RANDOM_STATE,
            n_jobs=-1,
        ),
        frame[features],
    ).fit(frame[features], frame["units_sold"])
    save_artifact(
        "demand_forecast.joblib",
        final_model,
        features,
        "units_sold",
        scores,
        "Calendar features are derived from the sales dates; demand lags use only prior daily sales.",
    )
    results["demand_forecast"] = scores


def train_expiry_risk(results: dict[str, Any]) -> None:
    frame = pd.read_csv(RAW_DIR / "inventory_batches.csv")
    frame["product_id"] = frame["product_id"].astype(str)
    features = [
        "product_id",
        "category",
        "days_to_expiry",
        "initial_quantity",
        "quantity_remaining",
        "avg_daily_sales_7d",
        "expected_demand_before_expiry",
        "unit_price",
        "unit_cost",
        "discount_pct",
    ]
    if "expiry_risk_label" in features or "waste_units_actual_simulated" in features:
        raise ValueError("Expiry target or post-outcome waste data leaked into input features")
    x = frame[features]
    y = frame["expiry_risk_label"].astype(int)
    x_train, x_test, y_train, y_test = train_test_split(
        x,
        y,
        test_size=0.2,
        random_state=RANDOM_STATE,
        stratify=y,
    )
    model = make_pipeline(
        RandomForestClassifier(
            n_estimators=300,
            min_samples_leaf=2,
            class_weight="balanced_subsample",
            random_state=RANDOM_STATE,
            n_jobs=-1,
        ),
        x_train,
    )
    model.fit(x_train, y_train)
    predicted = model.predict(x_test)
    probability = model.predict_proba(x_test)[:, 1]
    scores: dict[str, Any] = {
        "accuracy": float(accuracy_score(y_test, predicted)),
        "majority_class_baseline_accuracy": float(y_test.value_counts(normalize=True).max()),
        "balanced_accuracy": float(balanced_accuracy_score(y_test, predicted)),
        "precision": float(precision_score(y_test, predicted, zero_division=0)),
        "recall": float(recall_score(y_test, predicted, zero_division=0)),
        "f1": float(f1_score(y_test, predicted, zero_division=0)),
        "roc_auc": float(roc_auc_score(y_test, probability)),
        "train_rows": len(x_train),
        "test_rows": len(x_test),
        "split": "stratified random 80/20",
    }
    final_model = make_pipeline(
        RandomForestClassifier(
            n_estimators=300,
            min_samples_leaf=2,
            class_weight="balanced_subsample",
            random_state=RANDOM_STATE,
            n_jobs=-1,
        ),
        x,
    ).fit(x, y)
    save_artifact(
        "expiry_risk.joblib",
        final_model,
        features,
        "expiry_risk_label",
        scores,
        "expiry_risk_label and waste_units_actual_simulated are excluded from inputs.",
    )
    results["expiry_risk"] = scores


def train_food_waste(results: dict[str, Any]) -> None:
    frame = pd.read_csv(RAW_DIR / "perishable_inventory.csv", parse_dates=["date"])
    frame["product_id"] = frame["product_id"].astype(str)
    frame = frame.sort_values(["product_id", "date"]).reset_index(drop=True)
    available_fields = [
        "opening_stock",
        "units_received",
        "units_sold",
        "unit_price",
        "discount_pct",
        "days_to_expiry",
        "temperature_c",
        "stockout_flag",
    ]
    by_product = frame.groupby("product_id", sort=False)
    frame["previous_date"] = by_product["date"].shift(1)
    for field in available_fields:
        frame[f"previous_day_{field}"] = by_product[field].shift(1)
    consecutive_day = (frame["date"] - frame["previous_date"]).dt.days == 1
    frame = frame.loc[consecutive_day].copy()
    frame = add_calendar_features(frame)
    features = [
        "product_id",
        "category",
        "calendar_year",
        "calendar_month",
        "calendar_day_of_week",
        "calendar_day_of_year",
        "calendar_week_of_year",
        "calendar_is_weekend",
        "calendar_weekday_sin",
        "calendar_weekday_cos",
        "calendar_year_day_sin",
        "calendar_year_day_cos",
        "calendar_days_from_start",
        *[f"previous_day_{field}" for field in available_fields],
    ]
    if "waste_units" in features:
        raise ValueError("Food-waste target leaked into input features")
    train, test, cutoff = chronological_split(frame)
    model = make_pipeline(
        RandomForestRegressor(
            n_estimators=300,
            min_samples_leaf=2,
            random_state=RANDOM_STATE,
            n_jobs=-1,
        ),
        train[features],
    )
    model.fit(train[features], train["waste_units"])
    predicted = np.maximum(0, model.predict(test[features]))
    scores = regression_metrics(test["waste_units"], predicted)
    scores["zero_baseline_mae"] = float(
        mean_absolute_error(test["waste_units"], np.zeros(len(test)))
    )
    scores["train_rows"] = len(train)
    scores["test_rows"] = len(test)
    scores["test_start_date"] = cutoff
    scores["validation"] = "chronological rolling one-day-ahead; operational inputs are from the previous day"
    final_model = make_pipeline(
        RandomForestRegressor(
            n_estimators=300,
            min_samples_leaf=2,
            random_state=RANDOM_STATE,
            n_jobs=-1,
        ),
        frame[features],
    ).fit(frame[features], frame["waste_units"])
    save_artifact(
        "food_waste.joblib",
        final_model,
        features,
        "waste_units",
        scores,
        "All operational predictors are shifted to the previous calendar day; waste_units is never an input.",
    )
    results["food_waste"] = scores


def train_discount_prototype(results: dict[str, Any]) -> None:
    scenarios = pd.read_csv(RAW_DIR / "discount_scenarios_simulated.csv", dtype={"batch_id": str})
    batches = pd.read_csv(RAW_DIR / "inventory_batches.csv", dtype={"batch_id": str})
    batch_fields = ["batch_id", "category", "unit_price", "unit_cost"]
    frame = scenarios.merge(batches[batch_fields], on="batch_id", how="left", validate="many_to_one")
    frame["product_id"] = frame["product_id"].astype(str)
    features = [
        "product_id",
        "category",
        "days_to_expiry",
        "quantity_remaining",
        "discount_pct",
        "unit_price",
        "unit_cost",
    ]
    target = "estimated_gross_margin_simulated"
    x = frame[features]
    y = frame[target]
    splitter = GroupShuffleSplit(n_splits=1, test_size=0.2, random_state=RANDOM_STATE)
    train_indices, test_indices = next(splitter.split(x, y, groups=frame["batch_id"]))
    x_train, x_test = x.iloc[train_indices], x.iloc[test_indices]
    y_train, y_test = y.iloc[train_indices], y.iloc[test_indices]
    train_batches = set(frame.iloc[train_indices]["batch_id"])
    test_batches = set(frame.iloc[test_indices]["batch_id"])
    if train_batches & test_batches:
        raise ValueError("Discount scenarios for the same batch crossed the train/test split")
    model = make_pipeline(
        RandomForestRegressor(
            n_estimators=300,
            min_samples_leaf=2,
            random_state=RANDOM_STATE,
            n_jobs=-1,
        ),
        x_train,
    )
    model.fit(x_train, y_train)
    predicted = model.predict(x_test)
    scores = regression_metrics(y_test, predicted)
    scores["mean_target_baseline_mae"] = float(
        mean_absolute_error(y_test, np.full(len(y_test), y_train.mean()))
    )
    scores["train_rows"] = len(x_train)
    scores["test_rows"] = len(x_test)
    scores["train_batches"] = len(train_batches)
    scores["test_batches"] = len(test_batches)
    scores["validation"] = "grouped by batch_id; simulated scenario outcomes"
    final_model = make_pipeline(
        RandomForestRegressor(
            n_estimators=300,
            min_samples_leaf=2,
            random_state=RANDOM_STATE,
            n_jobs=-1,
        ),
        x,
    ).fit(x, y)
    save_artifact(
        "discount_recommendation_prototype.joblib",
        final_model,
        features,
        target,
        scores,
        "Prototype trained on simulated scenarios; scores are not evidence of real customer price response.",
    )

    inventory = batches.copy()
    inventory["product_id"] = inventory["product_id"].astype(str)
    inventory_features = inventory[
        ["batch_id", "product_id", "category", "days_to_expiry", "quantity_remaining", "unit_price", "unit_cost"]
    ]
    discount_levels = sorted(scenarios["discount_pct"].dropna().unique().tolist())
    candidates = []
    for discount in discount_levels:
        option = inventory_features.copy()
        option["discount_pct"] = discount
        option["predicted_simulated_gross_margin"] = final_model.predict(option[features])
        candidates.append(option)
    recommendations = pd.concat(candidates, ignore_index=True)
    best = recommendations.groupby("batch_id")["predicted_simulated_gross_margin"].idxmax()
    recommendations.loc[best, ["batch_id", "discount_pct", "predicted_simulated_gross_margin"]].to_csv(
        ARTIFACT_DIR / "discount_recommendations_prototype.csv", index=False
    )
    scores["recommendation_note"] = "Prototype recommendations maximize predicted simulated gross margin only."
    results["discount_recommendation_prototype"] = scores


def main() -> None:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    results: dict[str, Any] = {
        "data_root": "data/raw",
        "artifact_root": "artifacts",
        "discount_data_caveat": (
            "Discount scenarios are simulated. The model is a prototype and does not establish real customer price response."
        ),
    }
    train_demand_forecast(results)
    train_expiry_risk(results)
    train_food_waste(results)
    train_discount_prototype(results)
    (ARTIFACT_DIR / "metrics.json").write_text(
        json.dumps(results, indent=2, allow_nan=False) + "\n", encoding="utf-8"
    )
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()