
from pathlib import Path
import pandas as pd

BASE_DIR = Path(__file__).resolve().parents[2]
DATA_PATH = BASE_DIR / "ml" / "data" / "processed" / "perishable_features.csv"

df = pd.read_csv(DATA_PATH)

required_columns = [
    "product_id",
    "opening_stock",
    "units_received",
    "units_sold",
    "waste_units"
]

missing = [column for column in required_columns if column not in df.columns]

if missing:
    raise ValueError(f"Missing columns: {missing}")

df["stock_available"] = df["opening_stock"] + df["units_received"]
df["remaining_stock"] = (df["stock_available"] - df["units_sold"]).clip(lower=0)

summary = df.groupby("product_id").agg(
    total_available=("stock_available", "sum"),
    total_sold=("units_sold", "sum"),
    total_waste=("waste_units", "sum"),
    average_daily_sales=("units_sold", "mean"),
    average_remaining=("remaining_stock", "mean")
).reset_index()

summary["waste_rate_pct"] = (
    summary["total_waste"] / summary["total_available"].replace(0, pd.NA) * 100
).fillna(0).round(2)

summary["suggested_stock"] = (
    summary["average_daily_sales"] * 3
).round().astype(int)

summary = summary.sort_values("total_waste", ascending=False)

print("\nINVENTORY OPTIMIZATION REPORT")
print("=" * 60)
print(summary.to_string(index=False))

OUTPUT_PATH = BASE_DIR / "ml" / "data" / "processed" / "inventory_optimization.csv"
summary.to_csv(OUTPUT_PATH, index=False)

print(f"\nReport saved to: {OUTPUT_PATH}")
