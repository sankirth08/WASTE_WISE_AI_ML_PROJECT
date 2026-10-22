
from preprocessing import (
    PROCESSED,
    load_inventory,
    build_inventory_features
)

df = load_inventory()
df = build_inventory_features(df)

output = PROCESSED / "perishable_features.csv"
df.to_csv(output, index=False)

print("Feature engineering completed")
print(df.head())
print("Saved:", output)
