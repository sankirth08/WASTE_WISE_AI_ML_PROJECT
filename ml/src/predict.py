
from pathlib import Path
import pandas as pd
import joblib

BASE_DIR = Path(__file__).resolve().parents[2]
ARTIFACT_DIR = BASE_DIR / "ml" / "artifacts"

def predict_waste():
    model_path = ARTIFACT_DIR / "waste_prediction_model.pkl"

    if not model_path.exists():
        print("Waste model not found. Train the waste model first.")
        return

    model = joblib.load(model_path)

    print("\nEnter inventory details:")
    product_id = int(input("Product ID: "))
    category = input("Category: ")
    opening_stock = float(input("Opening stock: "))
    units_received = float(input("Units received: "))
    units_sold = float(input("Units sold: "))
    unit_price = float(input("Unit price: "))
    discount_pct = float(input("Discount percentage: "))
    days_to_expiry = float(input("Days to expiry: "))
    temperature_c = float(input("Temperature (C): "))

    stock_available = opening_stock + units_received
    remaining_after_sales = max(0, stock_available - units_sold)
    sales_rate = units_sold / stock_available if stock_available > 0 else 0
    expiry_urgency = 1 / (days_to_expiry + 1) if days_to_expiry >= 0 else 0

    today = pd.Timestamp.today()

    input_data = pd.DataFrame([{
        "product_id": product_id,
        "category": category,
        "opening_stock": opening_stock,
        "units_received": units_received,
        "units_sold": units_sold,
        "unit_price": unit_price,
        "discount_pct": discount_pct,
        "days_to_expiry": days_to_expiry,
        "temperature_c": temperature_c,
        "stock_available": stock_available,
        "remaining_after_sales": remaining_after_sales,
        "sales_rate": sales_rate,
        "expiry_urgency": expiry_urgency,
        "day_of_week": today.dayofweek,
        "month": today.month
    }])

    prediction = model.predict(input_data)[0]
    print(f"\nPredicted waste: {max(0, prediction):.2f} units")

def predict_discount_margin():
    model_path = ARTIFACT_DIR / "discount_model.pkl"

    if not model_path.exists():
        print("Discount model not found. Train the discount model first.")
        return

    model = joblib.load(model_path)

    print("\nEnter discount scenario details:")
    days_to_expiry = float(input("Days to expiry: "))
    quantity_remaining = float(input("Quantity remaining: "))
    discount_pct = float(input("Discount percentage: "))
    estimated_units_sold = float(input("Estimated units sold: "))

    input_data = pd.DataFrame([{
        "days_to_expiry": days_to_expiry,
        "quantity_remaining": quantity_remaining,
        "discount_pct": discount_pct,
        "estimated_units_sold_simulated": estimated_units_sold
    }])

    prediction = model.predict(input_data)[0]
    print(f"\nPredicted estimated gross margin: {prediction:.2f}")

while True:
    print("\n===== WASTEWISE AI PREDICTION =====")
    print("1. Predict food waste")
    print("2. Predict discount scenario gross margin")
    print("3. Exit")

    choice = input("Choose an option: ").strip()

    try:
        if choice == "1":
            predict_waste()
        elif choice == "2":
            predict_discount_margin()
        elif choice == "3":
            print("Exiting WasteWise AI.")
            break
        else:
            print("Invalid option. Enter 1, 2, or 3.")
    except (ValueError, KeyError) as error:
        print(f"Invalid input or model feature mismatch: {error}")
    except Exception as error:
        print(f"Prediction failed: {error}")
