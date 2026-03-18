import pandas as pd
import numpy as np
import pickle
import os
from datetime import datetime

def haversine(lat1, lon1, lat2, lon2):
    # Standard haversine formula to get distance in km
    R = 6371
    phi1, phi2 = np.radians(lat1), np.radians(lat2)
    dphi = np.radians(lat2 - lat1)
    dlambda = np.radians(lon2 - lon1)
    a = np.sin(dphi / 2)**2 + np.cos(phi1) * np.cos(phi2) * np.sin(dlambda / 2)**2
    return 2 * R * np.arctan2(np.sqrt(a), np.sqrt(1 - a))

def evaluate_on_real_data(input_path="Datasets/delivery_jl.csv", model_path="backend/ml_models/risk_model.pkl"):
    if not os.path.exists(model_path):
        print("Model not found. Please train the model first.")
        return
    
    print(f"Loading data from {input_path}...")
    df = pd.read_csv(input_path)
    
    # Load model
    with open(model_path, "rb") as f:
        model = pickle.load(f)
    
    print("Pre-processing features...")
    # Calculate distance (Acceptance to Delivery)
    df = df.dropna(subset=['accept_gps_lat', 'accept_gps_lng', 'delivery_gps_lat', 'delivery_gps_lng'])
    df['distance'] = haversine(df['accept_gps_lat'], df['accept_gps_lng'], 
                               df['delivery_gps_lat'], df['delivery_gps_lng'])
    
    # Calculate delivery time in minutes
    # Time format: 09-25 08:08:00
    def time_diff(row):
        try:
            fmt = "%m-%d %H:%M:%S"
            t1 = datetime.strptime(row['accept_time'], fmt)
            t2 = datetime.strptime(row['delivery_time'], fmt)
            delta = (t2 - t1).total_seconds() / 60
            return delta if delta > 0 else np.nan
        except:
            return np.nan

    df['delivery_duration'] = df.apply(time_diff, axis=1)
    df = df.dropna(subset=['delivery_duration'])
    
    # Simulate Missing Features (Traffic and Weather)
    # Traffic: 1 (Low) to 5 (High)
    # Weather: 0 (Clear), 1 (Rain), 2 (Storm)
    np.random.seed(42)
    df['traffic_level'] = np.random.randint(1, 6, len(df))
    df['weather_condition'] = np.random.randint(0, 3, len(df))
    
    # Prepare feature set for model
    # Note: Model expects columns: ["distance", "traffic_level", "delivery_time", "weather_condition"]
    X = df[["distance", "traffic_level", "delivery_duration", "weather_condition"]]
    X.columns = ["distance", "traffic_level", "delivery_time", "weather_condition"]
    
    print(f"Running predictions on {len(df)} samples...")
    df['predicted_risk'] = model.predict(X)
    
    probs = model.predict_proba(X)
    df['risk_probability'] = [max(p) for p in probs]
    
    # Summary
    print("\nEvaluation Summary")
    print("=" * 30)
    print(df['predicted_risk'].value_counts())
    
    output_path = "backend/data/evaluated_jilin.csv"
    df.to_csv(output_path, index=False)
    print(f"\nDetailed results saved to {output_path}")

if __name__ == "__main__":
    evaluate_on_real_data()
