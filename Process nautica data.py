import pandas as pd
import json
from datetime import datetime
import os

def process_nautica_data():
    """Process the downloaded Nautica Shopping Centre Excel file"""
    
    print("Processing Nautica data...")
    
    # Read the Excel file (skip first row which is the title, use row 2 as header)
    df = pd.read_excel('data/nautica_raw.xlsx', sheet_name=0, header=1)
    
    # Extract the columns we need
    # Column A: Statistical Period
    # Column E: PV Yield (kWh)
    # Column G: Export (kWh)
    # Column H: Import (kWh)
    
    df_clean = df[['Statistical Period', 'PV Yield (kWh)', 'Export (kWh)', 'Import (kWh)']].copy()
    
    # Rename columns for easier handling
    df_clean.columns = ['datetime', 'pv_yield', 'export', 'import']
    
    # Convert datetime to proper format
    df_clean['datetime'] = pd.to_datetime(df_clean['datetime'])
    
    # Replace NaN with 0 for calculations
    df_clean = df_clean.fillna(0)
    
    # Calculate daily totals
    daily_totals = {
        'pv_yield_total': float(df_clean['pv_yield'].sum()),
        'export_total': float(df_clean['export'].sum()),
        'import_total': float(df_clean['import'].sum()),
        'last_update': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'data_date': df_clean['datetime'].iloc[0].strftime('%Y-%m-%d')
    }
    
    # Convert to list of records for hourly data
    hourly_data = []
    for _, row in df_clean.iterrows():
        hourly_data.append({
            'datetime': row['datetime'].strftime('%Y-%m-%d %H:%M:%S'),
            'pv_yield': float(row['pv_yield']),
            'export': float(row['export']),
            'import': float(row['import'])
        })
    
    # Save processed data
    output = {
        'daily_totals': daily_totals,
        'hourly_data': hourly_data
    }
    
    # Ensure data directory exists
    os.makedirs('data', exist_ok=True)
    
    # Save as JSON
    with open('data/nautica_processed.json', 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f"Data processed successfully!")
    print(f"Date: {daily_totals['data_date']}")
    print(f"PV Yield: {daily_totals['pv_yield_total']:.2f} kWh")
    print(f"Export: {daily_totals['export_total']:.2f} kWh")
    print(f"Import: {daily_totals['import_total']:.2f} kWh")
    print(f"Hourly records: {len(hourly_data)}")
    
    return output

if __name__ == '__main__':
    process_nautica_data()
