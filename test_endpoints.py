import requests
import json
import io
import pandas as pd

# Test 1: Upload CSV
df = pd.DataFrame({
    'distance': [5.0, 10.0],
    'traffic_level': [2, 4],
    'delivery_time': [15.0, 30.0],
    'weather_condition': [0, 1],
    'lat': [12.9716, 12.9816],
    'lng': [77.5946, 77.6046],
    'id': [1, 2]
})

csv_data = df.to_csv(index=False)
files = {'file': ('test.csv', io.BytesIO(csv_data.encode('utf-8')), 'text/csv')}

try:
    print("Testing /upload_csv...")
    resp = requests.post("http://127.0.0.1:8000/upload_csv", files=files)
    print(resp.status_code)
    print(resp.text)
except Exception as e:
    print(f"Error: {e}")

# Test 2: Optimize Route
try:
    print("\nTesting /optimize_route...")
    data = {
        "deliveries": df.to_dict(orient="records")
    }
    resp2 = requests.post("http://127.0.0.1:8000/optimize_route", json=data)
    print(resp2.status_code)
    print(resp2.text)
except Exception as e:
    print(f"Error: {e}")
