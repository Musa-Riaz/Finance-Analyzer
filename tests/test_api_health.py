from fastapi.testclient import TestClient

from finance_analyzer.api.main import app


def _get_metrics_snapshot(client: TestClient) -> dict:
    response = client.get("/ops/metrics")
    assert response.status_code == 200
    return response.json()


def test_root_health_endpoint():
    client = TestClient(app)

    response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {"message": "Finance Analyzer API is running"}


def test_ops_metrics_endpoint_tracks_requests():
    client = TestClient(app)

    baseline = _get_metrics_snapshot(client)
    root_response = client.get("/")
    metrics_response = client.get("/ops/metrics")

    assert root_response.status_code == 200
    assert metrics_response.status_code == 200

    payload = metrics_response.json()
    assert payload["requests"]["total"] >= baseline["requests"]["total"] + 2
    assert payload["requests"]["success"] >= baseline["requests"]["success"] + 2
    assert payload["requests"]["failure"] >= 0
    assert payload["path_counts"].get("/") is not None
    assert payload["path_counts"].get("/ops/metrics") is not None


def test_request_id_header_is_propagated_and_generated():
    client = TestClient(app)

    custom_request_id = "phase5-test-request-id"
    custom_response = client.get("/", headers={"x-request-id": custom_request_id})
    generated_response = client.get("/")

    assert custom_response.status_code == 200
    assert custom_response.headers.get("x-request-id") == custom_request_id

    generated_request_id = generated_response.headers.get("x-request-id")
    assert generated_response.status_code == 200
    assert generated_request_id is not None
    assert generated_request_id != ""


def test_metrics_track_failure_status_for_missing_route():
    client = TestClient(app)

    baseline = _get_metrics_snapshot(client)
    missing_response = client.get("/does-not-exist")
    final = _get_metrics_snapshot(client)

    assert missing_response.status_code == 404
    assert final["requests"]["total"] >= baseline["requests"]["total"] + 2
    assert final["requests"]["failure"] >= baseline["requests"]["failure"] + 1
    assert int(final["status_counts"].get("404", 0)) >= int(
        baseline["status_counts"].get("404", 0)
    ) + 1
