
from pathlib import Path
import pandas as pd
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "ml" / "data" / "raw"
PROCESSED = ROOT / "ml" / "data" / "processed"
ARTIFACTS = ROOT / "ml" / "artifacts"

PROCESSED.mkdir(parents=True, exist_ok=True)
ARTIFACTS.mkdir(parents=True, exist_ok=True)

def load_inventory():
    path = RAW / "perishable_inventory.csv"
    if not path.exists():
        raise FileNotFoundError(f"Dataset not found: {path}")
    return pd.read_csv(path, parse_dates=["date"])

def load_discount_scenarios():
    path = RAW / "discount_scenarios_simulated.csv"
    if not path.exists():
        raise FileNotFoundError(f"Dataset not found: {path}")
    return pd.read_csv(path)

def build_inventory_features(df):
    df = df.copy()
    df["day_of_week"] = df["date"].dt.dayofweek
    df["month"] = df["date"].dt.month
    df["stock_available"] = df["opening_stock"] + df["units_received"]
    df["remaining_after_sales"] = (
        df["stock_available"] - df["units_sold"]
    ).clip(lower=0)
    df["sales_rate"] = (
        df["units_sold"] /
        df["stock_available"].replace(0, np.nan)
    ).fillna(0)
    df["expiry_urgency"] = 1 / (
        df["days_to_expiry"].clip(lower=0) + 1
    )
    return df

if __name__ == "__main__":
    df = build_inventory_features(load_inventory())
    output = PROCESSED / "perishable_features.csv"
    df.to_csv(output, index=False)
    print("Saved:", output)
