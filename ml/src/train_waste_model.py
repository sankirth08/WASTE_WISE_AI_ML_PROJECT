
from pathlib import Path

import pandas as pd
import joblib

from sklearn.model_selection import train_test_split
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score


BASE_DIR = Path(__file__).resolve().parents[2]
DATA_PATH = BASE_DIR / "ml" / "data" / "processed" / "perishable_features.csv"
ARTIFACT_DIR = BASE_DIR / "ml" / "artifacts"
MODEL_PATH = ARTIFACT_DIR / "waste_prediction_model.pkl"

ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)

df = pd.read_csv(DATA_PATH)
df["date"] = pd.to_datetime(df["date"], errors="coerce")
df = df.dropna(subset=["date", "waste_units"]).copy()

df["day_of_week"] = df["date"].dt.dayofweek
df["month"] = df["date"].dt.month

features = [
    "product_id",
    "category",
    "opening_stock",
    "units_received",
    "units_sold",
    "unit_price",
    "discount_pct",
    "days_to_expiry",
    "temperature_c",
    "stock_available",
    "remaining_after_sales",
    "sales_rate",
    "expiry_urgency",
    "day_of_week",
    "month"
]

X = df[features]
y = df["waste_units"]

categorical_features = ["category"]
numerical_features = [c for c in features if c not in categorical_features]

preprocessor = ColumnTransformer([
    (
        "categorical",
        Pipeline([
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("encoder", OneHotEncoder(handle_unknown="ignore"))
        ]),
        categorical_features
    ),
    (
        "numerical",
        Pipeline([
            ("imputer", SimpleImputer(strategy="median"))
        ]),
        numerical_features
    )
])

model = Pipeline([
    ("preprocessor", preprocessor),
    ("regressor", RandomForestRegressor(
        n_estimators=300,
        random_state=42,
        n_jobs=-1
    ))
])

df = df.sort_values("date")
split_index = int(len(df) * 0.8)

X_train = X.loc[df.index[:split_index]]
X_test = X.loc[df.index[split_index:]]
y_train = y.loc[df.index[:split_index]]
y_test = y.loc[df.index[split_index:]]

model.fit(X_train, y_train)

predictions = model.predict(X_test)

mae = mean_absolute_error(y_test, predictions)
rmse = mean_squared_error(y_test, predictions) ** 0.5
r2 = r2_score(y_test, predictions)

print("Food Waste Model Evaluation")
print("---------------------------")
print(f"MAE: {mae:.4f}")
print(f"RMSE: {rmse:.4f}")
print(f"R2 Score: {r2:.4f}")

joblib.dump(model, MODEL_PATH)
print(f"Model saved: {MODEL_PATH}")
