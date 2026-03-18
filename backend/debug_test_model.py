import pickle
import pandas as pd
import os

model_path = "backend/ml_models/risk_model.pkl"
test_data = pd.DataFrame([
    {"distance": 5.2, "traffic_level": 1, "delivery_time": 15, "weather_condition": 0},
    {"distance": 15.5, "traffic_level": 3, "delivery_time": 30, "weather_condition": 1},
    {"distance": 25.8, "traffic_level": 5, "delivery_time": 55, "weather_condition": 2}
])

if os.path.exists(model_path):
    with open(model_path, "rb") as f:
        model = pickle.load(f)
    predictions = model.predict(test_data)
    probabilities = model.predict_proba(test_data)
    
    print("Testing Model Directly")
    print("=" * 50)
    for i, pred in enumerate(predictions):
        print(f"Case {i+1}:")
        print(f"   Input: {test_data.iloc[i].to_dict()}")
        print(f"   Predicted Risk: {pred}")
        print(f"   Probability: {max(probabilities[i]):.2f}")
        print()
else:
    print(f"Model not found at {model_path}")
