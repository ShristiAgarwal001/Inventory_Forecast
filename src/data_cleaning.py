import pandas as pd
import numpy as np
from pathlib import Path

def clean_inventory_data(file_path):
    print("Loading raw dataset...")
    df = pd.read_excel(file_path)
    print(f"Original Dataset Shape: {df.shape}")

    initial_rows = len(df)
    df = df.drop_duplicates()
    print(f"Removed {initial_rows - len(df)} duplicate rows.")

    cat_cols = ['Category', 'Region', 'Weather Condition', 'Seasonality']
    for col in cat_cols:
        df[col] = df[col].astype(str).str.strip().str.title()
        df[col] = df[col].replace({'Nan': np.nan, 'None': np.nan})

    
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    missing_dates = df['Date'].isna().sum()
    df = df.dropna(subset=['Date'])
    print(f"Dropped {missing_dates} rows with invalid dates.")

    df.loc[df['Inventory Level'] < 0, 'Inventory Level'] = np.nan
    df.loc[df['Units Sold'] < 0, 'Units Sold'] = np.nan
    df.loc[(df['Discount'] < 0) | (df['Discount'] > 100), 'Discount'] = np.nan

   
    df.loc[df['Price'] > 1000, 'Price'] = np.nan

   
    df['Price'] = df.groupby('Category')['Price'].transform(lambda x: x.fillna(x.median()))
    df['Units Sold'] = df['Units Sold'].fillna(df['Units Sold'].median())
    df['Inventory Level'] = df['Inventory Level'].fillna(df['Inventory Level'].median())
    df['Category'] = df['Category'].fillna('Uncategorized')

    print(f"Cleaned Dataset Shape: {df.shape}")
    return df

if __name__ == "__main__":
    project_dir = Path(__file__).resolve().parent.parent
    input_path = project_dir / "data" / "rawdata" / "retail_store_inventory_extended_messy_2025_2026.xlsx"
    output_path = project_dir / "data" / "cleandata" / "retail_store_inventory_cleaned.csv"

    cleaned_df = clean_inventory_data(input_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    cleaned_df.to_csv(output_path, index=False)
    print(f"Cleaned data successfully saved to {output_path}")