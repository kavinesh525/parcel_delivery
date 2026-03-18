from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pandas as pd
import numpy as np
import pickle
from typing import List
import random
import math
import os
import io
from train_model import train_and_save_model

app = FastAPI()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "http://0.0.0.0:5173"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


model_path = "ml_models/risk_model.pkl"
if not os.path.exists(model_path):
    model_path = "backend/ml_models/risk_model.pkl"  
with open(model_path, "rb") as f:
    rf_model = pickle.load(f)

class DeliveryData(BaseModel):
    id: int
    distance: float
    traffic_level: int  
    delivery_time: float
    weather_condition: int 
    
    lat: float
    lng: float


class RouteRequest(BaseModel):
    deliveries: List[DeliveryData]

class FeedbackData(BaseModel):
    distance: float
    traffic_level: int  
    delivery_time: float
    weather_condition: int 
    actual_risk_level: str 

@app.get("/")
def read_root():
    return {"message": "Route Optimization System Active"}

@app.post("/predict_risk")
def predict_risk(data: DeliveryData):
   
    input_data = [[data.distance, data.traffic_level, data.delivery_time, data.weather_condition]]
    
  
    prediction = rf_model.predict(input_data)[0]
    
   
    probability = float(rf_model.predict_proba(input_data).max())
    
    return {
        "id": data.id,
        "risk_level": prediction, 
        "probability": probability
    }

@app.post("/feedback")
def submit_feedback(data: FeedbackData):
    """
    Ingest real-time data to improve the model.
    Appends the new data point to the dataset.
    """
    dataset_path = "backend/data/delivery_data.csv"
    
    
    new_data = {
        "distance": [data.distance],
        "traffic_level": [data.traffic_level],
        "delivery_time": [data.delivery_time],
        "weather_condition": [data.weather_condition],
        "risk_level": [data.actual_risk_level]
    }
    new_df = pd.DataFrame(new_data)
    
   
    if os.path.exists(dataset_path):
        new_df.to_csv(dataset_path, mode='a', header=False, index=False)
    else:
        new_df.to_csv(dataset_path, mode='w', header=True, index=False)
        
    return {"message": "Feedback received and data stored successfully."}

@app.post("/retrain")
def retrain_model():
    """
    Trigger model retraining using the latest dataset (including feedback).
    Reloads the model in memory without restarting the server.
    """
    global rf_model
    
    try:
        new_model, accuracy = train_and_save_model()
        if new_model:
            rf_model = new_model
            return {
                "message": "Model retrained and reloaded successfully.",
                "new_accuracy": accuracy
            }
        else:
            return {"error": "Training failed."}
    except Exception as e:
        return {"error": f"Retraining failed: {str(e)}"}

@app.post("/upload_csv")
async def upload_csv(file: UploadFile = File(...)):
    """
    Upload a CSV file with delivery data and get risk predictions + optimized route.
    
    Expected CSV columns:
    - distance (float): Distance in km
    - traffic_level (int): Traffic level 1-5
    - delivery_time (float): Delivery time in minutes
    - weather_condition (int): 0=Clear, 1=Rainy, 2=Stormy
    - lat (float): Latitude
    - lng (float): Longitude
    
    Optional columns:
    - id (int): Delivery ID (auto-generated if not provided)
    """
    try:
        
        contents = await file.read()
        df = pd.read_csv(io.BytesIO(contents))
        
       
        required_cols = ['distance', 'traffic_level', 'delivery_time', 'weather_condition', 'lat', 'lng']
        missing_cols = [col for col in required_cols if col not in df.columns]
        
        if missing_cols:
            return {
                "error": f"Missing required columns: {', '.join(missing_cols)}",
                "required_columns": required_cols
            }
        
        
        if 'id' not in df.columns:
            df['id'] = range(1, len(df) + 1)
        
       
        deliveries = []
        for _, row in df.iterrows():
            delivery = DeliveryData(
                id=int(row['id']),
                distance=float(row['distance']),
                traffic_level=int(row['traffic_level']),
                delivery_time=float(row['delivery_time']),
                weather_condition=int(row['weather_condition']),
                lat=float(row['lat']),
                lng=float(row['lng'])
            )
            deliveries.append(delivery)
        
        
        deliveries_with_risk = []
        
        
        if deliveries:
            input_data = [[d.distance, d.traffic_level, d.delivery_time, d.weather_condition] for d in deliveries]
            predictions = rf_model.predict(input_data)
            probabilities = rf_model.predict_proba(input_data).max(axis=1)
            
            for i, d in enumerate(deliveries):
                deliveries_with_risk.append({
                    "id": d.id,
                    "distance": d.distance,
                    "traffic_level": d.traffic_level,
                    "delivery_time": d.delivery_time,
                    "weather_condition": d.weather_condition,
                    "lat": d.lat,
                    "lng": d.lng,
                    "risk_level": predictions[i],
                    "risk_probability": float(probabilities[i])
                })
        
        n_deliveries = len(deliveries)
        

        if n_deliveries > 0:
            # Detect depot (stop with id == 1) so GA pins it as the first stop
            depot_idx = None
            for i, d in enumerate(deliveries_with_risk):
                if d.get("id", -1) == 1:
                    depot_idx = i
                    break

            best_route = run_genetic_algorithm(
                deliveries_with_risk,
                depot_idx=depot_idx,
                pop_size=80,
                n_generations=200,
                crossover_rate=0.85,
                mutation_rate=0.20,
                elite_size=5
            )

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
        
        return {
            "success": True,
            "total_deliveries": n_deliveries,
            "deliveries": deliveries_with_risk,
            "optimized_route": optimized_route,
            "message": f"Successfully processed {n_deliveries} deliveries from CSV"
        }
        
    except pd.errors.EmptyDataError:
        return {"error": "CSV file is empty"}
    except pd.errors.ParserError:
        return {"error": "Invalid CSV format"}
    except Exception as e:
        return {"error": f"Failed to process CSV: {str(e)}"}

def haversine(lat1, lon1, lat2, lon2):
    R = 6371
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))

def calculate_fitness(route, deliveries_with_risk):
    total_distance = 0
    total_risk_score = 0
    total_time = 0
    
    w1, w2, w3 = 0.5, 0.3, 0.2

    for i in range(len(route) - 1):
        idx1 = route[i]
        idx2 = route[i+1]
        
        d1 = deliveries_with_risk[idx1]
        d2 = deliveries_with_risk[idx2]
        
        
        geo_dist = haversine(d1["lat"], d1["lng"], d2["lat"], d2["lng"])
        total_distance += geo_dist
        
       
        risk_pred = d2["risk_level"]
        
        if risk_pred == "High":
            risk_penalty = 100
        elif risk_pred == "Medium":
            risk_penalty = 50
        else:
            risk_penalty = 10
            
        total_risk_score += (risk_penalty * d2["risk_probability"])
        total_time += d2["delivery_time"]
    

    first_node = deliveries_with_risk[route[0]]
    if first_node["risk_level"] == "High":
        total_risk_score += (100 * first_node["risk_probability"])
    elif first_node["risk_level"] == "Medium":
        total_risk_score += (50 * first_node["risk_probability"])
    else:
        total_risk_score += (10 * first_node["risk_probability"])
    
    total_time += first_node["delivery_time"]

    fitness = (w1 * total_distance) + (w2 * total_risk_score) + (w3 * total_time)
    return fitness

def create_population(n_deliveries, pop_size):
   
    population = []
    base_route = list(range(n_deliveries))
    for _ in range(pop_size):
        route = base_route.copy()
        random.shuffle(route)
        population.append(route)
    return population

def selection(population, fitnesses):
    
    k = 3
    selected = []
    for _ in range(len(population)):
       
        candidates_indices = random.sample(range(len(population)), k)
        
        
        best_idx = candidates_indices[0]
        for idx in candidates_indices[1:]:
            if fitnesses[idx] < fitnesses[best_idx]:
                best_idx = idx
                
        selected.append(population[best_idx])
    return selected

def crossover_ox1(parent1, parent2):
   
    size = len(parent1)
    if size < 2: return parent1
    
    start, end = sorted(random.sample(range(size), 2))
    
    child = [-1] * size
    
    child[start:end] = parent1[start:end]
    
    
    current_pos = end
    for gene in parent2:
        if gene not in child:
            if current_pos >= size:
                current_pos = 0
            child[current_pos] = gene
            current_pos += 1
            
    return child

def mutation_swap(route):
    """Swap two random genes (positions) in the route."""
    if len(route) < 2:
        return route
    idx1, idx2 = random.sample(range(len(route)), 2)
    route[idx1], route[idx2] = route[idx2], route[idx1]
    return route


def run_genetic_algorithm(deliveries_with_risk,
                          depot_idx=None,
                          pop_size=80,
                          n_generations=200,
                          crossover_rate=0.85,
                          mutation_rate=0.20,
                          elite_size=5):
    """
    Full Genetic Algorithm for TSP-style route optimisation.

    Strategy
    --------
    * If a depot is detected (id == 1), it is pinned as the first stop in
      every individual and only the remaining stops are evolved.
    * Elitism: the top `elite_size` individuals survive unchanged each gen.
    * Selection: tournament (k=3) via the existing selection().
    * Crossover: OX1 via crossover_ox1(); applied with probability crossover_rate.
    * Mutation:  swap mutation via mutation_swap(); applied with probability mutation_rate.
    """
    n = len(deliveries_with_risk)
    if n == 0:
        return []
    if n == 1:
        return [0]

  
    if depot_idx is not None:
        free_indices = [i for i in range(n) if i != depot_idx]
    else:
        free_indices = list(range(n))

    n_free = len(free_indices)

   
    def make_individual():
        seg = free_indices.copy()
        random.shuffle(seg)
        return seg

    def decode(individual):
        """Turn a free-segment individual into a full route."""
        if depot_idx is not None:
            return [depot_idx] + individual
        return individual

    def fitness(individual):
        return calculate_fitness(decode(individual), deliveries_with_risk)

    def cx(p1, p2):
        if n_free < 2:
            return p1[:]
        return crossover_ox1(p1, p2)

    def mut(ind):
        return mutation_swap(ind[:])

  
    population = [make_individual() for _ in range(pop_size)]
    fitnesses  = [fitness(ind) for ind in population]

    best_individual = min(population, key=fitness)
    best_fitness    = fitness(best_individual)

   
    for _ in range(n_generations):
        
        paired    = sorted(zip(fitnesses, population), key=lambda x: x[0])
        fitnesses = [p[0] for p in paired]
        population = [p[1] for p in paired]

        
        if fitnesses[0] < best_fitness:
            best_fitness    = fitnesses[0]
            best_individual = population[0][:]

        
        new_population = [ind[:] for ind in population[:elite_size]]
        new_fitnesses  = fitnesses[:elite_size]

        
        mating_pool = selection(population, fitnesses)

       
        i = 0
        while len(new_population) < pop_size:
            p1 = mating_pool[i % len(mating_pool)]
            p2 = mating_pool[(i + 1) % len(mating_pool)]
            i += 1

            
            if random.random() < crossover_rate:
                child = cx(p1, p2)
            else:
                child = p1[:]

            
            if random.random() < mutation_rate:
                child = mut(child)

            new_population.append(child)
            new_fitnesses.append(fitness(child))

        population = new_population
        fitnesses  = new_fitnesses

  
    return decode(best_individual)

@app.post("/optimize_route")
def optimize_route(request: RouteRequest):
    deliveries = request.deliveries
    n_deliveries = len(deliveries)
    
    if n_deliveries == 0:
        return {"optimized_route": []}
        
    deliveries_with_risk = []
    
    
    input_data = [[d.distance, d.traffic_level, d.delivery_time, d.weather_condition] for d in deliveries]
    predictions = rf_model.predict(input_data)
    probabilities = rf_model.predict_proba(input_data).max(axis=1)
    
    for i, d in enumerate(deliveries):
        deliveries_with_risk.append({
            "id": d.id,
            "distance": d.distance,
            "traffic_level": d.traffic_level,
            "delivery_time": d.delivery_time,
            "weather_condition": d.weather_condition,
            "lat": d.lat,
            "lng": d.lng,
            "risk_level": predictions[i],
            "risk_probability": float(probabilities[i])
        })
        
   
    depot_idx = None
    for i, d in enumerate(deliveries_with_risk):
        if d.get("id", -1) == 1:
            depot_idx = i
            break

    best_route = run_genetic_algorithm(
        deliveries_with_risk,
        depot_idx=depot_idx,
        pop_size=80,
        n_generations=200,
        crossover_rate=0.85,
        mutation_rate=0.20,
        elite_size=5
    )
        
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
        
    return {"optimized_route": optimized_route, "total_deliveries": n_deliveries}
