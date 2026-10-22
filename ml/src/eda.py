from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

BASE_DIR = Path(__file__).resolve().parents[2]
RAW_DIR = BASE_DIR / "ml" / "data" / "raw"
OUTPUT_DIR = BASE_DIR / "ml" / "data" / "processed"
PLOT_DIR = OUTPUT_DIR / "eda_plots"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
PLOT_DIR.mkdir(parents=True, exist_ok=True)

file_path = RAW_DIR / "perishable_inventory.csv"

if not file_path.exists():
    raise FileNotFoundError(f"Dataset not found: {file_path}")

df = pd.read_csv(file_path)
df["date"] = pd.to_datetime(df["date"], errors="coerce")
sns.set_theme(style="whitegrid")

print("Dataset shape:", df.shape)
print("\nMissing values:\n", df.isnull().sum())
print("\nSummary statistics:\n", df.describe(include="all").T)
print("\nTotal units sold:", df["units_sold"].sum())
print("Total waste units:", df["waste_units"].sum())

def save_plot(filename):
    plt.tight_layout()
    plt.savefig(PLOT_DIR / filename, dpi=200, bbox_inches="tight")
    plt.close()
    print("Saved:", filename)

# 1. Units sold distribution
plt.figure(figsize=(9, 5))
sns.histplot(data=df, x="units_sold", bins=25, kde=True)
plt.title("Distribution of Units Sold")
save_plot("01_units_sold_distribution.png")

# 2. Waste by product
waste_product = df.groupby("product_id", as_index=False)["waste_units"].sum()
waste_product = waste_product.sort_values("waste_units", ascending=False)

plt.figure(figsize=(9, 5))
sns.barplot(data=waste_product, x="product_id", y="waste_units")
plt.title("Total Waste by Product")
save_plot("02_waste_by_product.png")
waste_product.to_csv(OUTPUT_DIR / "eda_waste_by_product.csv", index=False)

# 3. Waste by category
waste_category = df.groupby("category", as_index=False)["waste_units"].sum()

plt.figure(figsize=(9, 5))
sns.barplot(data=waste_category, x="category", y="waste_units")
plt.title("Total Waste by Category")
plt.xticks(rotation=30)
save_plot("03_waste_by_category.png")
waste_category.to_csv(OUTPUT_DIR / "eda_waste_by_category.csv", index=False)

# 4. Daily sales and waste
daily = df.groupby("date", as_index=False).agg(
    units_sold=("units_sold", "sum"),
    waste_units=("waste_units", "sum")
)

plt.figure(figsize=(12, 5))
plt.plot(daily["date"], daily["units_sold"], label="Units Sold")
plt.plot(daily["date"], daily["waste_units"], label="Waste Units")
plt.title("Daily Sales and Waste")
plt.legend()
plt.xticks(rotation=45)
save_plot("04_daily_sales_and_waste.png")
daily.to_csv(OUTPUT_DIR / "eda_daily_sales_and_waste.csv", index=False)

# 5. Waste by days to expiry
expiry = df.groupby("days_to_expiry", as_index=False)["waste_units"].mean()

plt.figure(figsize=(9, 5))
sns.lineplot(data=expiry, x="days_to_expiry", y="waste_units", marker="o")
plt.title("Average Waste by Days to Expiry")
save_plot("05_waste_by_expiry.png")

# 6. Discount versus sales
discount = df.groupby("discount_pct", as_index=False)["units_sold"].mean()

plt.figure(figsize=(9, 5))
sns.barplot(data=discount, x="discount_pct", y="units_sold")
plt.title("Average Units Sold by Discount")
save_plot("06_discount_vs_sales.png")

# 7. Correlation heatmap
numeric_df = df.select_dtypes(include=np.number)

plt.figure(figsize=(11, 8))
sns.heatmap(numeric_df.corr(), annot=True, fmt=".2f", cmap="coolwarm")
plt.title("Numerical Feature Correlation")
save_plot("07_correlation_heatmap.png")

# 8. Waste occurrence by category
df["waste_occurred"] = (df["waste_units"] > 0).astype(int)
occurrence = df.groupby("category", as_index=False).agg(
    records=("waste_occurred", "size"),
    waste_records=("waste_occurred", "sum")
)
occurrence["waste_rate_pct"] = (
    occurrence["waste_records"] / occurrence["records"] * 100
)

plt.figure(figsize=(9, 5))
sns.barplot(data=occurrence, x="category", y="waste_rate_pct")
plt.title("Waste Occurrence Rate by Category")
plt.ylabel("Records with Waste (%)")
save_plot("08_waste_occurrence_by_category.png")
occurrence.to_csv(OUTPUT_DIR / "eda_waste_occurrence_by_category.csv", index=False)

# 9. Sales by stockout status
stockout = df.groupby("stockout_flag", as_index=False).agg(
    average_sales=("units_sold", "mean"),
    average_waste=("waste_units", "mean")
)
stockout["status"] = stockout["stockout_flag"].map({0: "No Stockout", 1: "Stockout"})

plt.figure(figsize=(8, 5))
sns.barplot(data=stockout, x="status", y="average_sales")
plt.title("Average Sales by Stockout Status")
save_plot("09_sales_by_stockout.png")
stockout.to_csv(OUTPUT_DIR / "eda_stockout_summary.csv", index=False)

print("\nEDA COMPLETED SUCCESSFULLY")
print("Charts saved in:", PLOT_DIR)
print("Reports saved in:", OUTPUT_DIR)
