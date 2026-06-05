import os
import glob
import pandas as pd
from dotenv import load_dotenv
from supabase import create_client, Client
import math

# Load environment variables
load_dotenv('.env')

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")

if not url or not key:
    print("Please set SUPABASE_URL and SUPABASE_KEY in your backend/.env file.")
    exit(1)

supabase: Client = create_client(url, key)

def clean_data(df):
    """Replace NaNs with None so Supabase inserts them as NULL"""
    return df.replace({float('nan'): None})

def chunked_insert(table_name, df, chunk_size=500):
    """Insert DataFrame into Supabase table in chunks"""
    records = str_dict_clean(df.to_dict('records'))
    
    total = len(records)
    for i in range(0, total, chunk_size):
        chunk = records[i:i + chunk_size]
        try:
            supabase.table(table_name).upsert(chunk).execute()
            print(f"Inserted chunk {i//chunk_size + 1}/{(total//chunk_size)+1} into {table_name}")
        except Exception as e:
            print(f"Error inserting into {table_name} at index {i}: {e}")

def str_dict_clean(records):
    """Ensure all floats/NaN are mapped to None properly for JSON serialization"""
    for row in records:
        for k, v in row.items():
            if type(v) == float and math.isnan(v):
                row[k] = None
                
            # Extra safeguard for converting integer floats to true ints during serialization
            if k == 'year' and row[k] is not None:
                row[k] = int(row[k])
                
    return records

def import_all_data():
    base_dir = "crawl_financial_downloads/output"
    
    # Types of reports to table mappings
    file_types = {
        # "_balance_sheet.csv": "financial_balance_sheets",
        # "_cash_flow.csv": "financial_cash_flows",
        "_financial_indicators.csv": "financial_indicators",
        # "_income_statement.csv": "financial_income_statements"
    }
    
    # Load all CSVs into aggregated dataframes
    for suffix, table_name in file_types.items():
        print(f"--- Loading data for {table_name} ---")
        files = glob.glob(os.path.join(base_dir, f"*{suffix}"))
        
        if not files:
            print(f"No files found for {suffix}")
            continue
            
        dfs = []
        for file in files:
            try:
                df = pd.read_csv(file)
                # Drop Unnamed columns (usually index exported by mistake)
                df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
                
                # Drop completely empty rows or rows missing critical identifiers
                if 'symbol' in df.columns:
                    df = df.dropna(subset=['symbol', 'year'])
                    
                # Make sure year is an integer, ignoring/dropping rows with missing year
                if 'year' in df.columns:
                    df['year'] = df['year'].astype(int)
                    
                # Primary key will be (symbol, year)
                if not df.empty:
                    dfs.append(df)
            except Exception as e:
                print(f"Could not read {file}: {e}")
                
        if dfs:
            combined_df = pd.concat(dfs, ignore_index=True)
            combined_df = clean_data(combined_df)
            
            # Print row count
            print(f"Total rows to insert for {table_name}: {len(combined_df)}")
            chunked_insert(table_name, combined_df)

if __name__ == "__main__":
    import_all_data()
    print("Data upload complete.")
