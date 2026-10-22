
from pathlib import Path
import pandas as pd
import joblib

from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

BASE_DIR = Path(__file__).resolve().parents[2]
DATA_PATH = BASE_DIR / "ml" / "data" / "raw" / "perishable_inventory.csv"
ARTIFACT_DIR = BASE_DIR / "ml" / "artifacts"
MODEL_PATH = ARTIFACT_DIR / "sales_forecast_model.pkl"
ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)

df = pd.read_csv(DATA_PATH)
df["date"] = pd.to_datetime(df["date"], errors="coerce")
df = df.dropna(subset=["date", "units_sold"]).sort_values("date").copy()

df["day_of_week"] = df["date"].dt.dayofweek
df["month"] = df["date"].dt.month
df["day_of_month"] = df["date"].dt.day

features = [
    "product_id",
    "opening_stock",
    "units_received",
    "unit_price",
    "discount_pct",
    "days_to_expiry",
    "temperature_c",
    "day_of_week",
    "month",
    "day_of_month"
]

target = "units_sold"

X = df[features]
y = df[target]

split_index = int(len(df) * 0.8)
X_train = X.iloc[:split_index]
X_test = X.iloc[split_index:]
y_train = y.iloc[:split_index]
y_test = y.iloc[split_index:]

model = RandomForestRegressor(
    n_estimators=200,
    random_state=42,
    n_jobs=-1
)

model.fit(X_train, y_train)
predictions = model.predict(X_test)

mae = mean_absolute_error(y_test, predictions)
rmse = mean_squared_error(y_test, predictions) ** 0.5
r2 = r2_score(y_test, predictions)

print("\nSALES FORECAST MODEL EVALUATION")
print("=" * 40)
print(f"Training rows: {len(X_train)}")
print(f"Testing rows: {len(X_test)}")
print(f"MAE: {mae:.4f}")
print(f"RMSE: {rmse:.4f}")
print(f"R2 Score: {r2:.4f}")

joblib.dump(model, MODEL_PATH)
print(f"\nModel saved: {MODEL_PATH}")

results = df.iloc[split_index:][["date", "product_id", "units_sold"]].copy()
results["predicted_units_sold"] = predictions.round(2)

OUTPUT_PATH = BASE_DIR / "ml" / "data" / "processed" / "sales_forecast_results.csv"
OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
results.to_csv(OUTPUT_PATH, index=False)

print(f"Forecast results saved: {OUTPUT_PATH}")
