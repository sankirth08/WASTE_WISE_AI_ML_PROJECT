
from preprocessing import RAW, load_inventory, load_discount_scenarios
import pandas as pd

def validate(name, df):
    print("\nDataset:", name)
    print("Shape:", df.shape)
    print("\nColumns:")
    print(df.columns.tolist())
    print("\nData types:")
    print(df.dtypes)
    print("\nMissing values:")
    print(df.isnull().sum())
    print("\nDuplicate rows:", df.duplicated().sum())
    print("\nStatistics:")
    print(df.describe(include="all"))

if __name__ == "__main__":
    validate("Perishable Inventory", load_inventory())
    validate("Discount Scenarios", load_discount_scenarios())

    for filename in ["calendar.csv", "sell_prices.csv", "products.csv"]:
        path = RAW / filename
        if path.exists():
            validate(filename, pd.read_csv(path, nrows=10000))
