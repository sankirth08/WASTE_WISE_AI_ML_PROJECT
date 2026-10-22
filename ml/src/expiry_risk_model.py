
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import joblib

from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    ConfusionMatrixDisplay
)

BASE_DIR = Path(r"D:\ai project\WasteWise-AI")

DATA_PATH = BASE_DIR / "ml" / "data" / "processed" / "perishable_features.csv"
OUTPUT_DIR = BASE_DIR / "ml" / "data" / "processed"
MODEL_DIR = BASE_DIR / "ml" / "artifacts"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
MODEL_DIR.mkdir(parents=True, exist_ok=True)

df = pd.read_csv(DATA_PATH)

print("Dataset shape:", df.shape)
print("Columns:", df.columns.tolist())

if "expiry_urgency" not in df.columns:
    raise ValueError(
        "The dataset must contain 'expiry_urgency'. "
        "Check your feature engineering output."
    )

if "days_to_expiry" in df.columns:
    days_left = pd.to_numeric(df["days_to_expiry"], errors="coerce")
elif "expiry_date" in df.columns and "date" in df.columns:
    days_left = (
        pd.to_datetime(df["expiry_date"], errors="coerce")
        - pd.to_datetime(df["date"], errors="coerce")
    ).dt.days
else:
    days_left = pd.to_numeric(df["expiry_urgency"], errors="coerce")

df["expiry_risk"] = (days_left <= 3).astype(int)
df.loc[days_left.isna(), "expiry_risk"] = np.nan

df = df.dropna(subset=["expiry_risk"]).copy()
df["expiry_risk"] = df["expiry_risk"].astype(int)

if df["expiry_risk"].nunique() < 2:
    raise ValueError(
        "Only one expiry-risk class was found. "
        "Check expiry dates or the expiry_urgency values."
    )

excluded = [
    "expiry_risk",
    "expiry_date",
    "date",
    "expiry_urgency"
]

features = [
    col for col in df.columns
    if col not in excluded
    and pd.api.types.is_numeric_dtype(df[col])
]

if not features:
    raise ValueError("No numeric input features found in the dataset.")

X = df[features].replace([np.inf, -np.inf], np.nan)
y = df["expiry_risk"]

valid = X.notna().any(axis=1)
X = X.loc[valid].copy()
y = y.loc[valid].copy()

X = X.fillna(X.median()).fillna(0)

if y.nunique() < 2:
    raise ValueError("The cleaned dataset contains only one risk class.")

split_index = int(len(df.loc[valid]) * 0.8)

if split_index <= 0 or split_index >= len(X):
    raise ValueError("Not enough rows to split into training and testing data.")

X_train = X.iloc[:split_index]
X_test = X.iloc[split_index:]
y_train = y.iloc[:split_index]
y_test = y.iloc[split_index:]

model = RandomForestClassifier(
    n_estimators=200,
    max_depth=12,
    class_weight="balanced",
    random_state=42,
    n_jobs=-1
)

model.fit(X_train, y_train)

predictions = model.predict(X_test)
probabilities = model.predict_proba(X_test)[:, list(model.classes_).index(1)]

print("\nEXPIRY RISK MODEL RESULTS")
print("-" * 35)
print("Training rows:", len(X_train))
print("Testing rows:", len(X_test))
print("Accuracy:", round(accuracy_score(y_test, predictions), 4))
print("\nClassification Report:")
print(classification_report(
    y_test,
    predictions,
    labels=[0, 1],
    target_names=["Low Risk", "High Risk"],
    zero_division=0
))

results = df.loc[X_test.index].copy()
results["actual_expiry_risk"] = y_test
results["predicted_expiry_risk"] = predictions
results["high_risk_probability"] = np.round(probabilities, 4)
results["risk_label"] = np.where(
    predictions == 1, "High Risk", "Low Risk"
)

results.to_csv(OUTPUT_DIR / "expiry_risk_predictions.csv", index=False)

joblib.dump(
    {
        "model": model,
        "features": features,
        "risk_definition": "High risk when days to expiry <= 3"
    },
    MODEL_DIR / "expiry_risk_model.joblib"
)

print("\nModel saved:", MODEL_DIR / "expiry_risk_model.joblib")
print("Predictions saved:", OUTPUT_DIR / "expiry_risk_predictions.csv")
print("\nSample predictions:")
print(results[[
    "actual_expiry_risk",
    "predicted_expiry_risk",
    "high_risk_probability",
    "risk_label"
]].head(10).to_string(index=False))

ConfusionMatrixDisplay.from_predictions(
    y_test,
    predictions,
    labels=[0, 1],
    display_labels=["Low Risk", "High Risk"]
)
plt.title("Expiry Risk - Confusion Matrix")
plt.tight_layout()
plt.show()

importance = pd.DataFrame({
    "feature": features,
    "importance": model.feature_importances_
}).sort_values("importance", ascending=False)

plt.figure(figsize=(10, 6))
plt.barh(importance["feature"], importance["importance"])
plt.title("Expiry Risk - Feature Importance")
plt.xlabel("Importance")
plt.gca().invert_yaxis()
plt.tight_layout()
plt.show()

print("\nExpiry risk model completed successfully!")
