import pandas as pd
import numpy as np

# Set random seed
np.random.seed(42)

# Generate synthetic data
n_samples = 1000
data = {
    "distance": np.random.uniform(1, 50, n_samples),
    "traffic_level": np.random.randint(1, 6, n_samples),
    "delivery_time": np.random.uniform(5, 120, n_samples),
    "weather_condition": np.random.randint(0, 3, n_samples),
}

df = pd.DataFrame(data)

# Risk calculation logic (simulate ground truth)
# High risk if high traffic OR stormy weather OR long distance + rain
def calculate_risk(row):
    score = (row["traffic_level"] * 10) + (row["weather_condition"] * 20) + (row["distance"] * 0.5)
    if score > 70:
        return "High"
    elif score > 40:
        return "Medium"
    else:
        return "Low"

df["risk_level"] = df.apply(calculate_risk, axis=1)

# Save to CSV
import os
os.makedirs("data", exist_ok=True)
df.to_csv("data/delivery_data.csv", index=False)
print("Synthetic delivery data generated.")
