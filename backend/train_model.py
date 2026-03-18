import pandas as pd
import os
import pickle
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score

def train_and_save_model(data_path="data/delivery_data.csv", model_path="ml_models/risk_model.pkl"):
    """
    Trains a Random Forest model on the delivery data after cleaning it.
    """
    if not os.path.exists(data_path):
        print(f"Data not found at {data_path}. Please ensure data exists.")
        return None

    
    df = pd.read_csv(data_path)
    
   
    initial_shape = df.shape
    
   
    df = df.drop_duplicates()
    
    
    df = df.dropna()
    
   
    cols_to_check = ["distance", "traffic_level", "delivery_time", "weather_condition"]
    for col in cols_to_check:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    
   
    df = df.dropna(subset=cols_to_check)
    
    cleaned_shape = df.shape
    if initial_shape != cleaned_shape:
        print(f"Dataset cleaned: {initial_shape[0] - cleaned_shape[0]} invalid/redundant rows removed.")
    else:
        print("Dataset checked: No missing values or duplicates found.")
   
    X = df[cols_to_check]
    y = df["risk_level"]

   
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

   
    rf_model = RandomForestClassifier(n_estimators=100, random_state=42)
    rf_model.fit(X_train, y_train)

   
    y_pred = rf_model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    print(f"Model accuracy: {accuracy:.2f}")

   
    os.makedirs(os.path.dirname(model_path), exist_ok=True)
    with open(model_path, "wb") as f:
        pickle.dump(rf_model, f)
    print(f"Model successfully saved to {model_path}")
    
    return rf_model, accuracy

if __name__ == "__main__":
    train_and_save_model()
