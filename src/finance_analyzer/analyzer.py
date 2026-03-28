import pandas as pd 

def get_summary(df: pd.DataFrame) -> dict:

    total_in = df[df["direction"] == "IN"]["amount"].sum()
    total_out = df[df["direction"] == "OUT"]["amount"].sum()
   
    return {
        "total_income": round(total_in, 2),
        "total_spent": round(abs(total_out), 2),
        "net": round(total_in - total_out, 2),
        "total_transactions": len(df),
        "avg_transaction": round(df["amount"].mean(), 2)
    }
    
def spending_by_type(df: pd.DataFrame) -> pd.DataFrame:
    """Spending by type"""
    # Group outgoing transactions by their TYPE (Raast Out, Mobile Top-Up, etc.)
    out = df[df["direction"] == "OUT"].copy()
    return(
        out.groupby("type")["amount"]
        .agg(total=lambda x: round(abs(x.sum()), 2), count="count")
        .sort_values("total", ascending=False)
    )    

def spending_by_day(df: pd.DataFrame) -> pd.DataFrame:
    out = df[df["direction"] == "OUT"].copy()
    return(
        out.groupby("day_of_week")["amount"]
        .agg(total=lambda x: round(abs(x.sum()), 2))
        .reindex(["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"])
        .fillna(0)
    )    

def biggest_expenses(df: pd.DataFrame, n: int = 5) -> pd.DataFrame:
    out = df[df["direction"] == "OUT"].copy()
    out["amount"] = out["amount"].abs()
    return out.nlargest(n, "amount")[["date", "description", "type", "amount"]]

def monthly_summary(df: pd.DataFrame) -> pd.DataFrame:
    results = []

    for month in sorted(df["month"].unique()):
        month_df = df[df["month"] == month]

        total_in = month_df[month_df["direction"] == "IN"]["amount"].sum()
        total_out = abs(month_df[month_df["direction"] == "OUT"]["amount"].sum())

        results.append({
            "month": month,
            "month_label": month_df["month_label"].iloc[0],
            "total_income": round(total_in, 2),
            "total_spent": round(total_out, 2),
            "net": round(total_in - total_out, 2),
            "num_transactions": len(month_df),
            "avg_transaction": round(month_df["amount"].abs().mean(), 2),
        })

    return pd.DataFrame(results)

def spending_by_type_summary(df: pd.DataFrame) -> pd.DataFrame:
    out = df[df["direction"] == "OUT"].copy()
    result = (
        out.groupby(["month", "month_label", "type"])["amount"]
        .apply(lambda x: round(abs(x.sum()), 2))
        .reset_index()
    )
    result.columns = ["month", "month_label", "type", "total_spent"]
    return result

def top_recipients(df: pd.DataFrame, n: int = 10) -> pd.DataFrame:
    out = df[df["direction"] == "OUT"].copy()

    # Extract the recipient name from the description
    # "Outgoing fund transfer to Jawad Khalid" → "Jawad Khalid"
    # str.replace() with regex=True lets us use a regex pattern
    # This strips the "Outgoing fund transfer to " prefix
    out["recipient"] = (
        out["description"]
        .str.replace("Outgoing fund transfer to ", "", regex=False)
        .str.replace("Paid to ", "", regex=False)
        .str.strip()
    )

    return (
        out.groupby("recipient")["amount"]
        .apply(lambda x: round(abs(x.sum()), 2))
        .sort_values(ascending=False)
        .head(n)  # .head(n) returns the first n rows — like .slice(0, n) in JS
        .reset_index()
        .rename(columns={"amount": "total_sent"})
    )