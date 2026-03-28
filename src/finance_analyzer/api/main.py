from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from finance_analyzer.api.routes import upload, analysis, forecast

app = FastAPI(
    title="Finance Analyzer API",
    description = "Personal Finance analysis with ML",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],   # allow all HTTP methods
    allow_headers=["*"],   # allow all headers
)

app.include_router(upload.router)
app.include_router(analysis.router)
app.include_router(forecast.router)

@app.get("/")
async def root():
    return {"message": "Finance Analyzer API is running"}