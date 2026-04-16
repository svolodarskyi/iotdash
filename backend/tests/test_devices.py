import uuid


def test_list_devices_empty(client):
    response = client.get("/api/devices")
    assert response.status_code == 200
    assert response.json() == []


def test_list_devices_with_data(client, seed_data):
    response = client.get("/api/devices")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    codes = {d["device_code"] for d in data}
    assert codes == {"test_sensor01", "test_sensor02"}


def test_get_device(client, seed_data):
    device_id = str(seed_data["devices"][0].id)
    response = client.get(f"/api/devices/{device_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["device_code"] == "test_sensor01"
    assert data["name"] == "Test Sensor 01"


def test_get_device_not_found(client):
    fake_id = str(uuid.uuid4())
    response = client.get(f"/api/devices/{fake_id}")
    assert response.status_code == 404
    assert response.json()["detail"] == "Device not found"


def test_get_device_embed_urls(client, seed_data):
    device_id = str(seed_data["devices"][0].id)
    response = client.get(f"/api/devices/{device_id}/embed-urls")
    assert response.status_code == 200
    data = response.json()
    assert data["device_code"] == "test_sensor01"
    assert len(data["urls"]) == 2  # 2 panel_ids in test dashboard
    assert "var-device_id=test_sensor01" in data["urls"][0]["url"]


def test_get_device_embed_urls_not_found(client):
    fake_id = str(uuid.uuid4())
    response = client.get(f"/api/devices/{fake_id}/embed-urls")
    assert response.status_code == 404
