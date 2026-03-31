import io
import os
from pathlib import Path

import pandas as pd
from fastapi import APIRouter, File, HTTPException, UploadFile

from finance_analyzer.api.db_native import persist_processed_dataframe
from finance_analyzer.loader import load_data
from finance_analyzer.cleaner import clean_transactions, add_month_column
from finance_analyzer.ml import (
    cluster_transactions,
    detect_anomalies,
)
from finance_analyzer.api.interfaces.models import UploadResponse

router = APIRouter(prefix="/upload", tags=["upload"])

_processed_df = None


def _cache_file_path() -> Path:
    configured = os.getenv("FINANCE_ANALYTICS_CACHE_PATH")
    if configured:
        return Path(configured)

    # routes/upload.py -> api -> finance_analyzer -> src -> repo root
    repo_root = Path(__file__).resolve().parents[4]
    return repo_root / "data" / "processed" / "processed_df.pkl"


def _persist_processed_df(df: pd.DataFrame) -> None:
    cache_path = _cache_file_path()
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_pickle(cache_path)


def clear_processed_df_cache() -> None:
    global _processed_df
    _processed_df = None


def get_processed_df():
    global _processed_df

    if _processed_df is not None:
        return _processed_df

    cache_path = _cache_file_path()
    if cache_path.exists():
        _processed_df = pd.read_pickle(cache_path)

    return _processed_df

@router.post("/", response_model=UploadResponse)

async def upload_files(files: list[UploadFile] = File(...)):
    global _processed_df

    if not files:
        raise HTTPException(status_code=400, detail="No File Uploaded")
    
    dataframes = []

    for file in files:
        #check the file type first
        if not file.filename.endswith("csv"):
            raise HTTPException(status_code=400,
            detail=f"{file.filename} is not a CSV file."
        )

        # read the file
        contents = await file.read()
        csv_file = io.StringIO(contents.decode("utf-8"))

        try:
            raw = load_data(csv_file)
            dataframes.append(raw)
        except Exception as e:  
            raise HTTPException(status_code=400,
            detail=f"Error processing {file.filename}: {str(e)}")
    
    #Combine all uploaded files
    combined = pd.concat(dataframes, ignore_index=True)

    #Run the full pipeline
    df = clean_transactions(combined)
    df = add_month_column(df)
    df = cluster_transactions(df)
    df = detect_anomalies(df)

    # Keep in-memory copy for backward-compatible local mode.
    _processed_df = df
    _persist_processed_df(df)

    source_label = ", ".join([file.filename for file in files])
    persist_processed_dataframe(df, source_label=source_label)

    months = sorted(df["month_label"].unique().tolist())

    return UploadResponse(
        message="Files uploaded and processed successfully",
        total_transactions=len(df),
        months_loaded=months
    )



