from pydantic import BaseModel
from typing import Optional

class Transaction(BaseModel):
    timestamp: str
    description: str
    amount: float
    direction: str
    category: Optional[str] = None
    is_anomaly: Optional[bool] = None
    anomaly_score: Optional[float] = None
    reason: Optional[str] = None

class Summary(BaseModel):
    total_income: float
    total_spent: float
    net: float
    total_transactions: int
    avg_transaction: float

class MonthlySummary(BaseModel):
    month: str
    month_label: str
    total_income: float
    total_spent: float
    net: float
    num_transactions: int

class CategoryBreakdown(BaseModel):
    category: str
    total: float
    count: int
    avg: float

class ForecastPoint(BaseModel):
    month_label: str
    predicted_spending: float
    is_forecast: bool

class ForecastResponse(BaseModel):
    trend_per_month: float
    avg_error: float
    months_trained: int
    points: list[ForecastPoint]

class UploadResponse(BaseModel):
    message: str
    months_loaded: list[str]
    total_transactions: int