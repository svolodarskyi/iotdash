"""Tests for the metrics endpoints."""


def test_list_metrics(auth_client):
    resp = auth_client.get("/api/metrics")
    assert resp.status_code == 200
    metrics = resp.json()
    assert len(metrics) == 3
    names = [m["name"] for m in metrics]
    assert "temperature" in names
    assert "humidity" in names
    assert "engine_rpm" in names


def test_list_metrics_unauthenticated(client, seed_data):
    resp = client.get("/api/metrics")
    assert resp.status_code == 401


def test_device_metrics(auth_client, seed_data):
    device_id = str(seed_data["devices"][0].id)
    resp = auth_client.get(f"/api/devices/{device_id}/metrics")
    assert resp.status_code == 200
    metrics = resp.json()
    assert len(metrics) == 1
    assert metrics[0]["metric_name"] == "temperature"
    assert metrics[0]["is_enabled"] is True


def test_device_metrics_empty(auth_client, seed_data):
    device_id = str(seed_data["devices"][1].id)
    resp = auth_client.get(f"/api/devices/{device_id}/metrics")
    assert resp.status_code == 200
    assert resp.json() == []
