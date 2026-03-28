# Read the CSV and return clean Dataframe
import os
import pandas as pd 

def load_data(file_path: str) -> pd.DataFrame:
    """Loading data from CSV"""
    try:
        df = pd.read_csv(
            file_path, 
            skiprows =  13,
            usecols = ["TIMESTAMP", "TYPE", "DESCRIPTION", "AMOUNT", "BALANCE"]
        )
        # skipping the first 13 rows as they contain metadata not needed
        print(f"Data loaded successfully from {file_path}")
        # Drop any completely empty rows that sneak in
        df = df.dropna(how="all")

        # removing whitespaces
        df.columns = df.columns.str.strip()
        return df
    except FileNotFoundError:
        print(f"Error: File not found at {file_path}")
        return None
    except Exception as e:
        print(f"Error: {e}")
        return None

def load_multiple_months(folder_path: str) -> pd.DataFrame:
    all_files = os.listdir(folder_path)
    csv_files = [f for f in all_files if f.endswith(".csv")]    
    if not csv_files:
        raise FileNotFoundError(f"No CSV files found in {folder_path}")
    #loading each csv individually and storing them in a list
    dataframes = []
    print("total number of files", csv_files)
    for fileName in csv_files:
        full_path = os.path.join(folder_path, fileName)
        raw = load_data(full_path)
        # We store the filename so we know which file each row came from
        # useful for debugging later
        raw["source_file"] = fileName
        dataframes.append(raw)

    return pd.concat(dataframes, ignore_index=True)
    
    