import pandas as pd 

def clean_transactions(df: pd.DataFrame) -> pd.DataFrame:
    # First, fixing timestamps
    df["TIMESTAMP"] = pd.to_datetime(df["TIMESTAMP"], format="%d/%m/%Y %H:%M")

    # Extract separate date and time columns for easier analysis later
    df["DATE"] = df["TIMESTAMP"].dt.date
    df["TIME"] = df["TIMESTAMP"].dt.time
    df["DAY_OF_WEEK"] = df["TIMESTAMP"].dt.day_name()
    df["WEEK"] = df["TIMESTAMP"].dt.isocalendar().week
    df["MONTH_DAY"] = df["TIMESTAMP"].dt.strftime("%b %d")  # e.g. "Jan 02"

    #Fixing amounts, removing columns from amounts

    df['AMOUNT']  = (
        df['AMOUNT'].
        astype(str).
        str.replace(",", "", regex=False).
        str.strip().
        astype(float)
    )

    # Fixing the balance
    df["BALANCE"] = (
        df["BALANCE"].
        astype(str).
        str.replace(",", "", regex=False).
        str.strip().
        astype(float)
    )

    # Cleaning the description
    df["DESCRIPTION"] = df["DESCRIPTION"].astype(str).str.split("\n").str[0].str.strip()

    # --- Add DIRECTION column ---
    # Positive amount = money in, negative = money out
    df["DIRECTION"] = df["AMOUNT"].apply(lambda x: "IN" if x > 0 else "OUT")

    # --- Rename columns to lowercase for convenience ---
    df.columns = df.columns.str.lower()

    return df

def add_month_column(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["month"] = df["timestamp"].dt.strftime("%Y-%m")
    df["month_label"] = df["timestamp"].dt.strftime("%b %Y")
    return df

