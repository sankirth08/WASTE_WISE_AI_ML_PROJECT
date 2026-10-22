
from sklearn.metrics import mean_absolute_error, mean_squared_error
import numpy as np

def regression_metrics(actual, predicted):
    actual = np.asarray(actual)
    predicted = np.asarray(predicted)

    mae = mean_absolute_error(actual, predicted)
    rmse = np.sqrt(mean_squared_error(actual, predicted))

    denominator = np.abs(actual).sum()
    wape = (
        np.abs(actual - predicted).sum() / denominator * 100
        if denominator > 0 else 0
    )

    return {
        "MAE": mae,
        "RMSE": rmse,
        "WAPE_percent": wape
    }

if __name__ == "__main__":
    actual = [10, 20, 30, 40]
    predicted = [12, 18, 28, 42]
    print(regression_metrics(actual, predicted))
