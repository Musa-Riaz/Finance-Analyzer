from fastapi import APIRouter, HTTPException
from finance_analyzer.api.db_native import load_processed_dataframe
from finance_analyzer.api.routes.upload import get_processed_df
from finance_analyzer.analyzer import get_summary, spending_by_type
from finance_analyzer.ml import spending_by_category, get_anomaly_report
from finance_analyzer.api.interfaces.models import (
    Summary,
    CategoryBreakdown,
    Transaction,
    MonthlySummary,
)
from finance_analyzer.ml import prepare_monthly_features

router = APIRouter(prefix="/analysis", tags={"analysis"})

def _check_data():
    # Helper to check if data has been uploaded yet
    # Reusable across all endpoints in this file
    df = load_processed_dataframe()
    if df is None:
        df = get_processed_df()
    if df is None:
        raise HTTPException(
            status_code=400,
            detail="No data loaded. Please upload CSV files first."
        )
    return df

@router.get("/summary", response_model = Summary)

async def summary():
    df = _check_data()
    result = get_summary(df)
    return Summary(**result)

@router.get("/monthly", response_model=list[MonthlySummary])

async def monthly():
    df = _check_data()
    from finance_analyzer.analyzer import monthly_summary
    result = monthly_summary(df)
    return [MonthlySummary(**row) for row in result.to_dict("records")]

@router.get("/categories", response_model = list[CategoryBreakdown])

async def categories():
    df = _check_data()
    result = spending_by_category(df)
    return [CategoryBreakdown(**row) for row in result.to_dict("records")]

@router.get("/anomalies", response_model = list[Transaction])

async def anomalies():
    df = _check_data()
    result = get_anomaly_report(df)
    # Convert timestamp to string because Pydantic needs string not datetime
    result["timestamp"] = result["timestamp"].astype(str)
    # Convert numpy bool to native Python bool
    result["is_anomaly"] = result["is_anomaly"].astype(bool)
    return [Transaction(**row) for row in result.to_dict("records")]
    
@router.get("/transactions", response_model = list[Transaction])

async def transactions():
    df = _check_data()
    # Return all transactions with their categories and anomaly flags
    cols = ["timestamp", "description", "amount", "direction",
            "category", "is_anomaly", "anomaly_score"]
    result = df[cols].copy()
    result["timestamp"] = result["timestamp"].astype(str)
    # Convert boolean numpy type to Python bool — Pydantic needs native Python types
    result["is_anomaly"] = result["is_anomaly"].astype(bool)
    return [Transaction(**row) for row in result.to_dict("records")]
