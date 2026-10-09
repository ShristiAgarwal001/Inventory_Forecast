from src.data_cleaning import clean_inventory_data
from src.analysis import run_data_analysis
from pathlib import Path

def main():
    print("=== Starting Retail Store Inventory Data Pipeline ===")
    project_dir = Path(__file__).resolve().parent
    
   
    raw_data_path = project_dir / "data" / "rawdata" / "retail_store_inventory_extended_messy_2025_2026.xlsx"
    cleaned_df = clean_inventory_data(raw_data_path)

    output_csv_path = project_dir / "data" / "cleandata" / "retail_store_inventory_cleaned.csv"
    output_csv_path.parent.mkdir(parents=True, exist_ok=True)
    cleaned_df.to_csv(output_csv_path, index=False)
    run_data_analysis(cleaned_df)
    
    print("\nData Analysis Pipeline Completed Successfully")

if __name__ == "__main__":
    main()