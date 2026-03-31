from pathlib import Path

from fastapi.testclient import TestClient

from finance_analyzer.api.main import app
from finance_analyzer.api.routes.upload import clear_processed_df_cache


SAMPLE_CSV = "\n".join(
    [
        *(["metadata"] * 13),
        "TIMESTAMP,TYPE,DESCRIPTION,AMOUNT,BALANCE",
        "02/01/2026 09:15,DEBIT,Coffee,-250,9750",
        "03/01/2026 11:00,DEBIT,Bus Fare,-120,9630",
        "04/01/2026 18:30,CREDIT,Salary,5000,14630",
        "07/01/2026 20:20,DEBIT,Dinner,-650,13980",
        "03/02/2026 10:00,DEBIT,Groceries,-1100,12880",
        "04/02/2026 09:10,DEBIT,Book Store,-300,12580",
        "05/02/2026 19:00,CREDIT,Freelance,2200,14780",
        "06/02/2026 21:40,DEBIT,Taxi,-180,14600",
    ]
)


def _upload_sample_data(client: TestClient) -> None:
    response = client.post(
        "/upload/",
        files={"files": ("sample.csv", SAMPLE_CSV.encode("utf-8"), "text/csv")},
    )
    assert response.status_code == 200


def test_analysis_summary_reads_from_persistent_cache(tmp_path: Path, monkeypatch):
    cache_path = tmp_path / "processed_df.pkl"
    monkeypatch.setenv("FINANCE_ANALYTICS_CACHE_PATH", str(cache_path))

    client = TestClient(app)
    _upload_sample_data(client)

    assert cache_path.exists()

    clear_processed_df_cache()

    response = client.get("/analysis/summary")

    assert response.status_code == 200
    payload = response.json()
    assert payload["total_transactions"] == 8


def test_forecast_survives_memory_reset_via_cache(tmp_path: Path, monkeypatch):
    cache_path = tmp_path / "processed_df.pkl"
    monkeypatch.setenv("FINANCE_ANALYTICS_CACHE_PATH", str(cache_path))

    client = TestClient(app)
    _upload_sample_data(client)

    clear_processed_df_cache()

    response = client.get("/forecast/?months_ahead=2")

    assert response.status_code == 200
    payload = response.json()
    assert payload["months_trained"] >= 2
    forecast_points = [point for point in payload["points"] if point["is_forecast"]]
    assert len(forecast_points) == 2
