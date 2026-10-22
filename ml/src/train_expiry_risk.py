
from pathlib import Path

import pandas as pd
import joblib

from sklearn.model_selection import train_test_split
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    classification_report,
    average_precision_score,
    precision_recall_curve,
    confusion_matrix
)


BASE_DIR = Path(__file__).resolve().parents[2]

DATA_PATH = (
    BASE_DIR
    / "ml"
    / "data"
    / "processed"
    / "perishable_features.csv"
)

ARTIFACT_DIR = BASE_DIR / "ml" / "artifacts"
MODEL_PATH = ARTIFACT_DIR / "expiry_risk_model.pkl"

ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)


df = pd.read_csv(DATA_PATH)

df["date"] = pd.to_datetime(df["date"], errors="coerce")
df = df.dropna(subset=["date", "waste_units"]).copy()

df["expiry_risk"] = (df["waste_units"] > 0).astype(int)

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

target = "expiry_risk"

X = df[features]
y = df[target]

if y.nunique() < 2:
    raise ValueError(
        "The target must contain both waste and no-waste records."
    )

categorical_features = ["category"]
numerical_features = [
    column for column in features
    if column not in categorical_features
]

preprocessor = ColumnTransformer(
    transformers=[
        (
            "categorical",
            Pipeline([
                (
                    "imputer",
                    SimpleImputer(strategy="most_frequent")
                ),
                (
                    "encoder",
                    OneHotEncoder(handle_unknown="ignore")
                )
            ]),
            categorical_features
        ),
        (
            "numerical",
            Pipeline([
                (
                    "imputer",
                    SimpleImputer(strategy="median")
                )
            ]),
            numerical_features
        )
    ]
)

model = Pipeline([
    ("preprocessor", preprocessor),
    (
        "classifier",
        RandomForestClassifier(
            n_estimators=300,
            class_weight="balanced",
            random_state=42,
            n_jobs=-1
        )
    )
])

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.30,
    random_state=42,
    stratify=y
)

print("Training expiry risk model...")

model.fit(X_train, y_train)

y_prob = model.predict_proba(X_test)[:, 1]

precision, recall, thresholds = precision_recall_curve(
    y_test,
    y_prob
)

if len(thresholds) > 0:
    f1_scores = (
        2 * precision[:-1] * recall[:-1]
        / (precision[:-1] + recall[:-1] + 1e-10)
    )

    best_index = f1_scores.argmax()
    best_threshold = float(thresholds[best_index])
else:
    best_threshold = 0.5

y_pred = (y_prob >= best_threshold).astype(int)

print("\nExpiry Risk Model Evaluation")
print("----------------------------")

print(f"Selected threshold: {best_threshold:.4f}")

print(
    classification_report(
        y_test,
        y_pred,
        labels=[0, 1],
        target_names=["No Waste", "Waste"],
        zero_division=0
    )
)

print("Confusion Matrix:")
print(confusion_matrix(y_test, y_pred, labels=[0, 1]))

pr_auc = average_precision_score(y_test, y_prob)

print(f"PR-AUC: {pr_auc:.4f}")

joblib.dump(
    {
        "model": model,
        "threshold": best_threshold
    },
    MODEL_PATH
)

print(f"\nExpiry risk model saved: {MODEL_PATH}")
