"""Tests for admin device endpoints."""

from tests.conftest import (
    DEVICE_TYPE_ENGINE_MONITOR_ID,
    DEVICE_TYPE_TEMP_SENSOR_ID,
    METRIC_HUMIDITY_ID,
    METRIC_RPM_ID,
    METRIC_TEMP_ID,
)


def test_list_devices(admin_client, seed_data):
    resp = admin_client.get("/api/admin/devices")
    assert resp.status_code == 200
    devices = resp.json()
    assert len(devices) >= 2


def test_list_device_type_names(admin_client, seed_data):
    resp = admin_client.get("/api/admin/devices/device-types")
    assert resp.status_code == 200
    types = resp.json()
    assert "temperature_sensor" in types


def test_list_devices_filter_by_device_type_id(admin_client, seed_data):
    dt_id = str(DEVICE_TYPE_TEMP_SENSOR_ID)
    resp = admin_client.get(f"/api/admin/devices?device_type_id={dt_id}")
    assert resp.status_code == 200
    devices = resp.json()
    assert all(d["device_type_id"] == dt_id for d in devices)


def test_list_devices_filter_by_metric_name(admin_client, seed_data):
    resp = admin_client.get("/api/admin/devices?metric_name=temperature")
    assert resp.status_code == 200
    devices = resp.json()
    assert len(devices) >= 1
    for d in devices:
        metric_names = [m["metric_name"] for m in d["metrics"]]
        assert "temperature" in metric_names


def test_list_devices_filter_by_nonexistent_metric(admin_client, seed_data):
    resp = admin_client.get("/api/admin/devices?metric_name=nonexistent")
    assert resp.status_code == 200
    assert resp.json() == []


def test_list_devices_combined_filters(admin_client, seed_data):
    org_id = str(seed_data["org"].id)
    dt_id = str(DEVICE_TYPE_TEMP_SENSOR_ID)
    resp = admin_client.get(f"/api/admin/devices?org_id={org_id}&device_type_id={dt_id}")
    assert resp.status_code == 200
    devices = resp.json()
    assert all(d["organisation_id"] == org_id for d in devices)
    assert all(d["device_type_id"] == dt_id for d in devices)


def test_provision_device_auto_code(admin_client, seed_data):
    org_id = str(seed_data["org"].id)
    dt_id = str(DEVICE_TYPE_TEMP_SENSOR_ID)
    resp = admin_client.post("/api/admin/devices", json={
        "name": "New Device",
        "organisation_id": org_id,
        "device_type_id": dt_id,
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["device_code"].startswith("dev-")
    assert data["name"] == "New Device"
    assert data["device_type_id"] == dt_id
    assert data["device_type_name"] == "temperature_sensor"


def test_provision_device_manual_code(admin_client, seed_data):
    org_id = str(seed_data["org"].id)
    dt_id = str(DEVICE_TYPE_TEMP_SENSOR_ID)
    resp = admin_client.post("/api/admin/devices", json={
        "name": "Manual Device",
        "device_code": "my-custom-uid",
        "organisation_id": org_id,
        "device_type_id": dt_id,
    })
    assert resp.status_code == 201
    assert resp.json()["device_code"] == "my-custom-uid"


def test_provision_device_duplicate_code(admin_client, seed_data):
    org_id = str(seed_data["org"].id)
    dt_id = str(DEVICE_TYPE_TEMP_SENSOR_ID)
    resp = admin_client.post("/api/admin/devices", json={
        "name": "Dup Device",
        "device_code": "test_sensor01",
        "organisation_id": org_id,
        "device_type_id": dt_id,
    })
    assert resp.status_code == 409


def test_provision_device_with_metrics(admin_client, seed_data):
    org_id = str(seed_data["org"].id)
    dt_id = str(DEVICE_TYPE_TEMP_SENSOR_ID)
    resp = admin_client.post("/api/admin/devices", json={
        "name": "Metric Device",
        "organisation_id": org_id,
        "device_type_id": dt_id,
        "metric_ids": [str(METRIC_TEMP_ID), str(METRIC_HUMIDITY_ID)],
    })
    assert resp.status_code == 201
    data = resp.json()
    metric_names = [m["metric_name"] for m in data["metrics"]]
    assert "temperature" in metric_names
    assert "humidity" in metric_names


def test_provision_device_invalid_metric_for_type(admin_client, seed_data):
    """Cannot assign engine_rpm to a temperature_sensor device type."""
    org_id = str(seed_data["org"].id)
    dt_id = str(DEVICE_TYPE_TEMP_SENSOR_ID)
    resp = admin_client.post("/api/admin/devices", json={
        "name": "Bad Metric Device",
        "organisation_id": org_id,
        "device_type_id": dt_id,
        "metric_ids": [str(METRIC_RPM_ID)],
    })
    assert resp.status_code == 400
    assert "not supported" in resp.json()["detail"]


def test_provision_device_auto_enable(admin_client, seed_data, mock_mqtt):
    org_id = str(seed_data["org"].id)
    dt_id = str(DEVICE_TYPE_TEMP_SENSOR_ID)
    resp = admin_client.post("/api/admin/devices", json={
        "name": "Auto Device",
        "organisation_id": org_id,
        "device_type_id": dt_id,
        "metric_ids": [str(METRIC_TEMP_ID)],
        "auto_enable": True,
    })
    assert resp.status_code == 201
    mock_mqtt.sync_device_metrics.assert_called_once()
    call_args = mock_mqtt.sync_device_metrics.call_args
    metrics_state = call_args[0][1]
    # temperature enabled, humidity disabled (both are device type metrics)
    assert metrics_state["temperature"] == 1
    assert metrics_state["humidity"] == 0


def test_update_device(admin_client, seed_data):
    device_id = str(seed_data["devices"][0].id)
    resp = admin_client.put(f"/api/admin/devices/{device_id}", json={"name": "Updated Name"})
    assert resp.status_code == 200
    assert resp.json()["name"] == "Updated Name"


def test_update_device_type(admin_client, seed_data):
    """Can change device type to engine_monitor."""
    device_id = str(seed_data["devices"][0].id)
    new_dt_id = str(DEVICE_TYPE_ENGINE_MONITOR_ID)
    resp = admin_client.put(f"/api/admin/devices/{device_id}", json={
        "device_type_id": new_dt_id,
    })
    assert resp.status_code == 200
    assert resp.json()["device_type_id"] == new_dt_id
    assert resp.json()["device_type_name"] == "engine_monitor"


def test_update_device_metrics(admin_client, seed_data):
    device_id = str(seed_data["devices"][0].id)
    resp = admin_client.patch(f"/api/admin/devices/{device_id}/metrics", json={
        "metric_ids": [str(METRIC_TEMP_ID), str(METRIC_HUMIDITY_ID)],
        "send_config": False,
    })
    assert resp.status_code == 200
    metric_names = [m["metric_name"] for m in resp.json()["metrics"]]
    assert "temperature" in metric_names
    assert "humidity" in metric_names


def test_update_device_metrics_invalid_for_type(admin_client, seed_data):
    """Cannot assign engine_rpm to a temperature_sensor device."""
    device_id = str(seed_data["devices"][0].id)
    resp = admin_client.patch(f"/api/admin/devices/{device_id}/metrics", json={
        "metric_ids": [str(METRIC_RPM_ID)],
        "send_config": False,
    })
    assert resp.status_code == 400
    assert "not supported" in resp.json()["detail"]


def test_update_device_metrics_sync_mqtt(admin_client, seed_data, mock_mqtt):
    """When send_config=True, sends full metrics state to device."""
    device_id = str(seed_data["devices"][0].id)
    # device1 currently has temperature. Add humidity.
    resp = admin_client.patch(f"/api/admin/devices/{device_id}/metrics", json={
        "metric_ids": [str(METRIC_TEMP_ID), str(METRIC_HUMIDITY_ID)],
        "send_config": True,
    })
    assert resp.status_code == 200
    mock_mqtt.sync_device_metrics.assert_called_once()
    call_args = mock_mqtt.sync_device_metrics.call_args
    metrics_state = call_args[0][1]
    assert metrics_state["temperature"] == 1
    assert metrics_state["humidity"] == 1


def test_update_device_metrics_sync_mqtt_remove(admin_client, seed_data, mock_mqtt):
    """When removing all metrics, sends full state with all disabled."""
    device_id = str(seed_data["devices"][0].id)
    # device1 currently has temperature. Remove it (empty list).
    resp = admin_client.patch(f"/api/admin/devices/{device_id}/metrics", json={
        "metric_ids": [],
        "send_config": True,
    })
    assert resp.status_code == 200
    mock_mqtt.sync_device_metrics.assert_called_once()
    call_args = mock_mqtt.sync_device_metrics.call_args
    metrics_state = call_args[0][1]
    # All device type metrics should be disabled
    assert metrics_state["temperature"] == 0
    assert metrics_state["humidity"] == 0


def test_sync_device_config(admin_client, seed_data, mock_mqtt):
    device_id = str(seed_data["devices"][0].id)
    resp = admin_client.post(f"/api/admin/devices/{device_id}/sync-config")
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert "temperature" in data["metrics_sent"]
    mock_mqtt.sync_device_metrics.assert_called_once()
    call_args = mock_mqtt.sync_device_metrics.call_args
    metrics_state = call_args[0][1]
    assert metrics_state["temperature"] == 1
    assert metrics_state["humidity"] == 0


def test_delete_device(admin_client, seed_data):
    device_id = str(seed_data["devices"][1].id)
    resp = admin_client.delete(f"/api/admin/devices/{device_id}")
    assert resp.status_code == 204


def test_viewer_cannot_provision(auth_client, seed_data):
    org_id = str(seed_data["org"].id)
    dt_id = str(DEVICE_TYPE_TEMP_SENSOR_ID)
    resp = auth_client.post("/api/admin/devices", json={
        "name": "Nope",
        "organisation_id": org_id,
        "device_type_id": dt_id,
    })
    assert resp.status_code == 403


# ── Device Types CRUD ─────────────────────────────────

def test_list_device_types_crud(admin_client, seed_data):
    resp = admin_client.get("/api/admin/device-types")
    assert resp.status_code == 200
    types = resp.json()
    assert len(types) >= 2
    names = [t["name"] for t in types]
    assert "temperature_sensor" in names
    assert "engine_monitor" in names
    # Check allowed metrics are included
    temp_type = next(t for t in types if t["name"] == "temperature_sensor")
    metric_names = [m["metric_name"] for m in temp_type["allowed_metrics"]]
    assert "temperature" in metric_names
    assert "humidity" in metric_names


def test_create_device_type(admin_client, seed_data):
    resp = admin_client.post("/api/admin/device-types", json={
        "name": "pressure_sensor",
        "description": "Pressure measurement device",
        "metric_ids": [str(METRIC_TEMP_ID)],
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "pressure_sensor"
    assert len(data["allowed_metrics"]) == 1


def test_create_device_type_duplicate(admin_client, seed_data):
    resp = admin_client.post("/api/admin/device-types", json={
        "name": "temperature_sensor",
    })
    assert resp.status_code == 409


def test_update_device_type(admin_client, seed_data):
    dt_id = str(DEVICE_TYPE_TEMP_SENSOR_ID)
    resp = admin_client.put(f"/api/admin/device-types/{dt_id}", json={
        "description": "Updated description",
    })
    assert resp.status_code == 200
    assert resp.json()["description"] == "Updated description"


def test_delete_device_type_blocked_by_devices(admin_client, seed_data):
    """Cannot delete device type that has provisioned devices."""
    dt_id = str(DEVICE_TYPE_TEMP_SENSOR_ID)
    resp = admin_client.delete(f"/api/admin/device-types/{dt_id}")
    assert resp.status_code == 409


def test_delete_device_type_no_devices(admin_client, seed_data):
    """Can delete device type with no provisioned devices."""
    # Create a new device type with no devices
    resp = admin_client.post("/api/admin/device-types", json={
        "name": "deletable_type",
    })
    assert resp.status_code == 201
    dt_id = resp.json()["id"]

    resp = admin_client.delete(f"/api/admin/device-types/{dt_id}")
    assert resp.status_code == 204
