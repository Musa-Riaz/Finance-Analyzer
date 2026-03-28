from fastapi import APIRouter, UploadFile, File, HTTPException
import pandas as pd 
import io
import os 
import shutil

from finance_analyzer.loader import load_data
from finance_analyzer.cleaner import clean_transactions, add_month_column
from finance_analyzer.ml import (
    prepare_text_features,
    cluster_transactions,
    detect_anomalies,
)
from finance_analyzer.api.interfaces.models import UploadResponse

router = APIRouter(prefix="/upload", tags=["upload"])

_processed_df = None

def get_processed_df():
    return _processed_df

@router.post("/", response_model = UploadResponse)

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

    #Store in memory
    _processed_df = df
    months = sorted(df["month_label"].unique().tolist())

    return UploadResponse(
        message="Files uploaded and processed successfully",
        total_transactions=len(df),
        months_loaded=months
    )



