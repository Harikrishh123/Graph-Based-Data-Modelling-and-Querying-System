import os
import sqlite3
import pandas as pd
import json

DATA_DIR = r"D:\Dodge\sap-order-to-cash-dataset\sap-o2c-data"
DB_PATH = r"D:\Dodge\o2c-graph-app\o2c.db"

def ingest():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    conn = sqlite3.connect(DB_PATH)
    
    for table_name in os.listdir(DATA_DIR):
        table_path = os.path.join(DATA_DIR, table_name)
        if not os.path.isdir(table_path):
            continue
            
        print(f"Ingesting table: {table_name}")
        records = []
        for file_name in os.listdir(table_path):
            if file_name.endswith('.jsonl'):
                file_path = os.path.join(table_path, file_name)
                with open(file_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        if line.strip():
                            records.append(json.loads(line))
        
        if records:
            df = pd.DataFrame(records)
            for col in df.columns:
                if df[col].apply(lambda x: isinstance(x, (dict, list))).any():
                    df[col] = df[col].apply(lambda x: json.dumps(x) if isinstance(x, (dict, list)) else x)
            df.to_sql(table_name, conn, if_exists='replace', index=False)
            print(f"Inserted {len(df)} records into {table_name}")
    
    conn.close()
    print("Ingestion complete.")

if __name__ == "__main__":
    ingest()
