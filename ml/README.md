# Model training

From the `ml` directory, train all models and write their artifacts with:

```powershell
python src/train_models.py
```

The script evaluates models on held-out data, then refits each model on all eligible rows before saving it under `artifacts/`. Demand and food-waste evaluation holds out the latest 20% of dates. The demand score is rolling one-day-ahead and assumes that the day's price and promotion are known. Food-waste operational inputs are shifted to the previous calendar day; its date-derived calendar features describe the prediction date. Expiry risk uses a stratified split and excludes both `expiry_risk_label` and `waste_units_actual_simulated` from its inputs.

`discount_recommendation_prototype.joblib` and `discount_recommendations_prototype.csv` are based on simulated discount scenarios. Their metrics and recommendations are prototype results, not evidence of real customer price response. Review `artifacts/metrics.json` before using any model operationally.