import pandas as pd
import os

def analyze_data(data_path="backend/data/delivery_data.csv"):
    if not os.path.exists(data_path):
        print(f"Data not found at {data_path}")
        return
    
    df = pd.read_csv(data_path)
    
    print("Dataset Analysis")
    print("=" * 30)
    print(f"Total Rows: {len(df)}")
    print("\nMissing Values:")
    print(df.isnull().sum())
    
    print("\nDuplicate Rows:", df.duplicated().sum())
    
    print("\nSummary Statistics:")
    print(df.describe())
    
    print("\nRisk Level Distribution:")
    print(df["risk_level"].value_counts())

if __name__ == "__main__":
    analyze_data()
