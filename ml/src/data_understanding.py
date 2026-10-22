from pathlib import Path
import pandas as pd

BASE_DIR = Path(__file__).resolve().parents[2]
RAW_DIR = BASE_DIR / "ml" / "data" / "raw"
OUTPUT_DIR = BASE_DIR / "ml" / "data" / "processed"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

files = [
    "perishable_inventory.csv",
    "discount_scenarios_simulated.csv",
    "calendar.csv",
    "sell_prices.csv",
    "products.csv"
]

reports = []
missing_reports = []

for filename in files:
    path = RAW_DIR / filename

    if not path.exists():
        print(f"\nFILE NOT FOUND: {path}")
        continue

    df = pd.read_csv(path)

    print("\n" + "=" * 60)
    print("DATASET:", filename)
    print("=" * 60)
    print("Shape:", df.shape)
    print("\nFirst five rows:")
    print(df.head().to_string())
    print("\nData types:")
    print(df.dtypes)
    print("\nMissing values:")
    print(df.isnull().sum())
    print("\nDuplicate rows:", df.duplicated().sum())
    print("\nSummary statistics:")
    print(df.describe(include="all").T.to_string())

    reports.append({
        "Dataset": filename,
        "Rows": len(df),
        "Columns": len(df.columns),
        "Missing_Values": int(df.isnull().sum().sum()),
        "Duplicate_Rows": int(df.duplicated().sum())
    })

    for column in df.columns:
        missing_reports.append({
            "Dataset": filename,
            "Column": column,
            "Missing_Count": int(df[column].isnull().sum()),
            "Missing_Percentage": round(
                df[column].isnull().mean() * 100, 2
            )
        })

    if filename == "perishable_inventory.csv":
        if "date" in df.columns:
            dates = pd.to_datetime(df["date"], errors="coerce")
            print("\nDate range:", dates.min(), "to", dates.max())

        if "units_sold" in df.columns:
            print("Total units sold:", df["units_sold"].sum())

        if "waste_units" in df.columns:
            print("Total waste units:", df["waste_units"].sum())

            if "product_id" in df.columns:
                print("\nWaste by product:")
                print(
                    df.groupby("product_id")["waste_units"]
                    .sum()
                    .sort_values(ascending=False)
                )

if reports:
    pd.DataFrame(reports).to_csv(
        OUTPUT_DIR / "data_understanding_report.csv", index=False
    )

    pd.DataFrame(missing_reports).to_csv(
        OUTPUT_DIR / "missing_values_report.csv", index=False
    )

    print("\nFINAL DATASET REPORT")
    print(pd.DataFrame(reports).to_string(index=False))
    print("\nReports saved to:", OUTPUT_DIR)
    print("DATA UNDERSTANDING COMPLETED SUCCESSFULLY")
else:
    print("\nNo datasets loaded. Check the location of your CSV files.")
