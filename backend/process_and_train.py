import pandas as pd
import os
import train_model

def main():
    print("Loading data from 'new dataset' folder...")
    dataset_path = '../new dataset/synthetic_last_mile_delivery_dataset.csv'
    
    if not os.path.exists(dataset_path):
        print(f"Error: {dataset_path} not found.")
        return
        
    df_new = pd.read_csv(dataset_path)

    # Rename columns to match the expected format
    df_new = df_new.rename(columns={
        'distance_km': 'distance',
        'traffic_level': 'traffic_level',
        'delivery_time_window_min': 'delivery_time',
        'weather_severity': 'weather_condition'
    })

    # Drop any rows missing core fields
    cols = ['distance', 'traffic_level', 'delivery_time', 'weather_condition']
    df_new = df_new.dropna(subset=cols)

    # Ensure weather_condition maps comfortably to 0-2 for our current pipeline
    # (0=Clear, 1=Rain, 2=Storm)
    df_new['weather_condition'] = df_new['weather_condition'].apply(lambda x: min(2, x))

    # Calculate risk_level. If the delivery actually failed in the historical dataset, we mark it as High Risk.
    # Otherwise, we use the standard mathematical simulation logic to balance the distribution.
    def compute_risk(row):
        if row.get('delivery_failed', 0) == 1:
            return "High"
            
        score = (row["traffic_level"] * 10) + (row["weather_condition"] * 20) + (row["distance"] * 0.5)
        if score > 70:
            return "High"
        elif score > 40:
            return "Medium"
        else:
            return "Low"

    df_new['risk_level'] = df_new.apply(compute_risk, axis=1)
    
    # Save the expanded dataset back so the next APIs can use it natively
    os.makedirs("data", exist_ok=True)
    df_new[cols + ['risk_level']].to_csv('data/delivery_data.csv', index=False)
    
    print(f"Data transformed. Successfully saved {len(df_new)} advanced samples to delivery_data.csv.")
    
    print("Initiating model training algorithm on the new data...")
    train_model.train_and_save_model()

if __name__ == "__main__":
    main()
