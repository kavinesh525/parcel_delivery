from flask import Flask, request, jsonify
from flask_cors import CORS
import pandas as pd
import numpy as np
import pickle
import math
import os
import io
import random
from train_model import train_and_save_model

app = Flask(__name__)


CORS(app, resources={r"/*": {"origins": ["http://localhost:5173", "http://127.0.0.1:5173", "http://0.0.0.0:5173"]}}, supports_credentials=True)


model_path = "ml_models/risk_model.pkl"
if not os.path.exists(model_path):
    model_path = "backend/ml_models/risk_model.pkl"  
with open(model_path, "rb") as f:
    rf_model = pickle.load(f)


def haversine(lat1, lon1, lat2, lon2):
    R = 6371
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))

@app.route("/", methods=["GET"])
def read_root():
    return jsonify({"message": "Route Optimization System Active"})

@app.route("/predict_risk", methods=["POST"])
def predict_risk():
    data = request.get_json()
    
    input_data = [[
        data.get("distance"), 
        data.get("traffic_level"), 
        data.get("delivery_time"), 
        data.get("weather_condition")
    ]]
    
    prediction = rf_model.predict(input_data)[0]
    probability = float(rf_model.predict_proba(input_data).max())
    
    return jsonify({
        "id": data.get("id"),
        "risk_level": prediction, 
        "probability": probability
    })

@app.route("/feedback", methods=["POST"])
def submit_feedback():
    data = request.get_json()
    dataset_path = "backend/data/delivery_data.csv"
    
    new_data = {
        "distance": [data["distance"]],
        "traffic_level": [data["traffic_level"]],
        "delivery_time": [data["delivery_time"]],
        "weather_condition": [data["weather_condition"]],
        "risk_level": [data["actual_risk_level"]]
    }
    new_df = pd.DataFrame(new_data)
    
    header = not os.path.exists(dataset_path)
    new_df.to_csv(dataset_path, mode='a' if not header else 'w', header=header, index=False)
        
    return jsonify({"message": "Feedback received and data stored successfully."})

@app.route("/retrain", methods=["POST"])
def retrain_model():
    global rf_model
    try:
        new_model, accuracy = train_and_save_model()
        if new_model:
            rf_model = new_model
            return jsonify({
                "message": "Model retrained and reloaded successfully.",
                "new_accuracy": accuracy
            })
        else:
            return jsonify({"error": "Training failed."}), 500
    except Exception as e:
        return jsonify({"error": f"Retraining failed: {str(e)}"}), 500

@app.route("/upload_csv", methods=["POST"])
def upload_csv():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
        
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    try:
        contents = file.read()
        df = pd.read_csv(io.BytesIO(contents))
        
        required_cols = ['distance', 'traffic_level', 'delivery_time', 'weather_condition', 'lat', 'lng']
        missing_cols = [col for col in required_cols if col not in df.columns]
        
        if missing_cols:
            return jsonify({
                "error": f"Missing required columns: {', '.join(missing_cols)}",
                "required_columns": required_cols
            })
            
        if 'id' not in df.columns:
            df['id'] = range(1, len(df) + 1)
            
        deliveries = []
        for _, row in df.iterrows():
            deliveries.append({
                "id": int(row['id']),
                "distance": float(row['distance']),
                "traffic_level": int(row['traffic_level']),
                "delivery_time": float(row['delivery_time']),
                "weather_condition": int(row['weather_condition']),
                "lat": float(row['lat']),
                "lng": float(row['lng'])
            })
            
        deliveries_with_risk = []
        if deliveries:
            input_data = [[d["distance"], d["traffic_level"], d["delivery_time"], d["weather_condition"]] for d in deliveries]
            predictions = rf_model.predict(input_data)
            probabilities = rf_model.predict_proba(input_data).max(axis=1)
            
            for i, d in enumerate(deliveries):
                d_copy = d.copy()
                d_copy.update({
                    "risk_level": predictions[i],
                    "risk_probability": float(probabilities[i])
                })
                deliveries_with_risk.append(d_copy)
        
        n_deliveries = len(deliveries)
        
        if n_deliveries > 0 and n_deliveries <= 100:
            depot_idx = next((i for i, d in enumerate(deliveries_with_risk) if d.get("id", -1) == 1), None)
                    
            def greedy_hybrid_tsp(deliveries_list):
                if not deliveries_list: return []
                unvisited = set(range(len(deliveries_list)))
                route = []
                
                curr = depot_idx if depot_idx is not None else list(unvisited)[0]
                route.append(curr)
                unvisited.remove(curr)
                
                while unvisited:
                    d1 = deliveries_list[curr]
                    best_next = None
                    best_cost = float('inf')
                    
                    for nxt in unvisited:
                        d2 = deliveries_list[nxt]
                        dist = haversine(d1["lat"], d1["lng"], d2["lat"], d2["lng"])
                        
                        risk = d2["risk_level"]
                        penalty = 15.0 if risk == "High" else 5.0 if risk == "Medium" else 0.0
                            
                        cost = dist + penalty
                        if cost < best_cost:
                            best_cost = cost
                            best_next = nxt
                            
                    route.append(best_next)
                    unvisited.remove(best_next)
                    curr = best_next
                    
                return route

            best_route = greedy_hybrid_tsp(deliveries_with_risk)
        else:
            best_route = list(range(n_deliveries))
            
        features = []
        for idx in best_route:
            d_info = deliveries_with_risk[idx]
            features.append({
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [d_info["lng"], d_info["lat"]]
                },
                "properties": {
                    "stop_id": d_info["id"],
                    "index": int(idx),
                    "risk_level": d_info["risk_level"],
                    "risk_probability": d_info["risk_probability"],
                    "distance": d_info["distance"],
                    "traffic": d_info["traffic_level"],
                    "weather": d_info["weather_condition"]
                }
            })
            
        optimized_route = {
            "type": "FeatureCollection",
            "features": features
        }
        
        return jsonify({
            "success": True,
            "total_deliveries": n_deliveries,
            "deliveries": deliveries_with_risk,
            "optimized_route": optimized_route,
            "message": f"Successfully processed {n_deliveries} deliveries from CSV"
        })
        
    except pd.errors.EmptyDataError:
        return jsonify({"error": "CSV file is empty"}), 400
    except Exception as e:
        return jsonify({"error": f"Failed to process CSV: {str(e)}"}), 500

@app.route("/optimize_route", methods=["POST"])
def optimize_route():
    data = request.get_json()
    deliveries = data.get("deliveries", [])
    n_deliveries = len(deliveries)
    
    if n_deliveries == 0:
        return jsonify({"optimized_route": [], "total_deliveries": 0})
        
    deliveries_with_risk = []
    
    input_data = [[d["distance"], d["traffic_level"], d["delivery_time"], d["weather_condition"]] for d in deliveries]
    predictions = rf_model.predict(input_data)
    probabilities = rf_model.predict_proba(input_data).max(axis=1)
    
    for i, d in enumerate(deliveries):
        d_copy = d.copy()
        d_copy.update({
            "risk_level": predictions[i],
            "risk_probability": float(probabilities[i])
        })
        deliveries_with_risk.append(d_copy)
        
    if n_deliveries <= 100:
        depot_idx = next((i for i, d in enumerate(deliveries_with_risk) if d.get("id", -1) == 1), None)
                
        def greedy_hybrid_tsp(deliveries_list):
            if not deliveries_list: return []
            unvisited = set(range(len(deliveries_list)))
            route = []
            
            curr = depot_idx if depot_idx is not None else list(unvisited)[0]
            route.append(curr)
            unvisited.remove(curr)
            
            while unvisited:
                d1 = deliveries_list[curr]
                best_next = None
                best_cost = float('inf')
                
                for nxt in unvisited:
                    d2 = deliveries_list[nxt]
                    dist = haversine(d1["lat"], d1["lng"], d2["lat"], d2["lng"])
                    
                    risk = d2["risk_level"]
                    penalty = 15.0 if risk == "High" else 5.0 if risk == "Medium" else 0.0
                        
                    cost = dist + penalty
                    if cost < best_cost:
                        best_cost = cost
                        best_next = nxt
                        
                route.append(best_next)
                unvisited.remove(best_next)
                curr = best_next
                
            return route

        best_route = greedy_hybrid_tsp(deliveries_with_risk)
    else:
        best_route = list(range(n_deliveries))
        
    features = []
    for idx in best_route:
        d_info = deliveries_with_risk[idx]
        features.append({
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [d_info["lng"], d_info["lat"]]
            },
            "properties": {
                "stop_id": d_info.get("id", d_info.get("stop_id")),
                "index": int(idx),
                "risk_level": d_info["risk_level"],
                "risk_probability": d_info["risk_probability"],
                "distance": d_info["distance"],
                "traffic": d_info["traffic_level"], 
                "weather": d_info["weather_condition"]
            }
        })
        
    optimized_route = {
        "type": "FeatureCollection",
        "features": features
    }
        
    return jsonify({"optimized_route": optimized_route, "total_deliveries": n_deliveries})

if __name__ == "__main__":
    app.run(debug=True, port=8000)
