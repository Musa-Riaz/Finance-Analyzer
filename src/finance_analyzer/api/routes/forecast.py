from fastapi import APIRouter, HTTPException, Query
from ..db_native import load_processed_dataframe
from .upload import get_processed_df
from ...ml import prepare_monthly_features, train_spending_model, forecast_next_months
from ..interfaces.models import ForecastResponse, ForecastPoint

router = APIRouter(prefix="/forecast", tags=["forecast"])

@router.get("/", response_model=ForecastResponse)

async def forecast(months_ahead: int = Query(default=3, ge=1, le=12)):

    df = load_processed_dataframe()
    if df is None:
        df = get_processed_df()
    if df is None:
        raise HTTPException(
            status_code = 400,
            detail="No data loaded"
        )
    
    try:
        monthly = prepare_monthly_features(df)
        if len(monthly) < 2:
            raise HTTPException(
                status_code=422,
                detail="Need at least 2 months of data for forecasting"
            )
        model, metadata = train_spending_model(monthly)
        forecast_df = forecast_next_months(model, monthly, n_months=months_ahead)
        # Convert forecast DataFrame rows to ForecastPoint objects
        points = [
            ForecastPoint(**row)
            for row in forecast_df[["month_label", "predicted_spending", "is_forecast"]]
            .to_dict("records")
        ]

        return ForecastResponse(
            trend_per_month=metadata["slope"],
            avg_error=metadata["avg_loo_error"],
            months_trained=metadata["num_months_trained"],
            points=points,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Forecast failed: {str(e)}"
        )   

        

