import uuid


# ── CRUD Tests ─────────────────────────────────────────


def test_list_alerts_unauthenticated(client):
    response = client.get("/api/alerts")
    assert response.status_code == 401


def test_list_alerts_empty(auth_client, seed_data):
    response = auth_client.get("/api/alerts")
    assert response.status_code == 200
    assert response.json() == []


def test_create_alert(auth_client, seed_data, seed_user):
    device_id = str(seed_data["devices"][0].id)
    body = {
        "device_id": device_id,
        "metric": "temperature",
        "condition": "above",
        "threshold": 30.0,
        "duration_seconds": 60,
        "notification_email": "test@example.com",
    }
    response = auth_client.post("/api/alerts", json=body)
    assert response.status_code == 201
    data = response.json()
    assert data["device_id"] == device_id
    assert data["metric"] == "temperature"
    assert data["condition"] == "above"
    assert data["threshold"] == 30.0
    assert data["duration_seconds"] == 60
    assert data["notification_email"] == "test@example.com"
    assert data["is_enabled"] is True
    assert data["created_by"] == str(seed_user.id)
    assert data["grafana_rule_uid"] == "test-rule-uid"
    assert data["device_code"] == "test_sensor01"


def test_create_alert_device_not_found(auth_client, seed_data):
    body = {
        "device_id": str(uuid.uuid4()),
        "metric": "temperature",
        "condition": "above",
        "threshold": 30.0,
        "notification_email": "test@example.com",
    }
    response = auth_client.post("/api/alerts", json=body)
    assert response.status_code == 404


def test_get_alert(auth_client, seed_data, seed_user):
    device_id = str(seed_data["devices"][0].id)
    create_resp = auth_client.post(
        "/api/alerts",
        json={
            "device_id": device_id,
            "metric": "temperature",
            "condition": "above",
            "threshold": 25.0,
            "notification_email": "test@example.com",
        },
    )
    alert_id = create_resp.json()["id"]

    response = auth_client.get(f"/api/alerts/{alert_id}")
    assert response.status_code == 200
    assert response.json()["id"] == alert_id
    assert response.json()["threshold"] == 25.0


def test_get_alert_not_found(auth_client, seed_data):
    response = auth_client.get(f"/api/alerts/{uuid.uuid4()}")
    assert response.status_code == 404


def test_update_alert(auth_client, seed_data, seed_user):
    device_id = str(seed_data["devices"][0].id)
    create_resp = auth_client.post(
        "/api/alerts",
        json={
            "device_id": device_id,
            "metric": "temperature",
            "condition": "above",
            "threshold": 30.0,
            "notification_email": "test@example.com",
        },
    )
    alert_id = create_resp.json()["id"]

    response = auth_client.put(
        f"/api/alerts/{alert_id}",
        json={"threshold": 28.0, "duration_seconds": 120},
    )
    assert response.status_code == 200
    assert response.json()["threshold"] == 28.0
    assert response.json()["duration_seconds"] == 120


def test_delete_alert(auth_client, seed_data, seed_user):
    device_id = str(seed_data["devices"][0].id)
    create_resp = auth_client.post(
        "/api/alerts",
        json={
            "device_id": device_id,
            "metric": "temperature",
            "condition": "above",
            "threshold": 30.0,
            "notification_email": "test@example.com",
        },
    )
    alert_id = create_resp.json()["id"]

    response = auth_client.delete(f"/api/alerts/{alert_id}")
    assert response.status_code == 204

    # Confirm it's gone
    response = auth_client.get(f"/api/alerts/{alert_id}")
    assert response.status_code == 404


def test_toggle_alert(auth_client, seed_data, seed_user):
    device_id = str(seed_data["devices"][0].id)
    create_resp = auth_client.post(
        "/api/alerts",
        json={
            "device_id": device_id,
            "metric": "temperature",
            "condition": "above",
            "threshold": 30.0,
            "notification_email": "test@example.com",
        },
    )
    alert_id = create_resp.json()["id"]

    # Disable
    response = auth_client.patch(
        f"/api/alerts/{alert_id}/toggle",
        json={"is_enabled": False},
    )
    assert response.status_code == 200
    assert response.json()["is_enabled"] is False

    # Re-enable
    response = auth_client.patch(
        f"/api/alerts/{alert_id}/toggle",
        json={"is_enabled": True},
    )
    assert response.status_code == 200
    assert response.json()["is_enabled"] is True


def test_list_alerts_returns_created(auth_client, seed_data, seed_user):
    device_id = str(seed_data["devices"][0].id)
    auth_client.post(
        "/api/alerts",
        json={
            "device_id": device_id,
            "metric": "temperature",
            "condition": "above",
            "threshold": 30.0,
            "notification_email": "test@example.com",
        },
    )
    response = auth_client.get("/api/alerts")
    assert response.status_code == 200
    assert len(response.json()) == 1


# ── Org Isolation Tests ─────────────────────────────────


def _login(client, email, password):
    """Login and return the client with cookies set."""
    resp = client.post("/api/auth/login", json={"email": email, "password": password})
    assert resp.status_code == 200
    return client


def test_org_a_sees_only_own_alerts(client, two_org_seed):
    _login(client, "user_a@orga.com", "passa123")
    response = client.get("/api/alerts")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["device_code"] == "org_a_sensor"


def test_org_b_sees_only_own_alerts(client, two_org_seed):
    _login(client, "user_b@orgb.com", "passb123")
    response = client.get("/api/alerts")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["device_code"] == "org_b_sensor"


def test_org_a_cannot_get_org_b_alert(client, two_org_seed):
    _login(client, "user_a@orga.com", "passa123")
    alert_b_id = str(two_org_seed["alert_b"].id)
    response = client.get(f"/api/alerts/{alert_b_id}")
    assert response.status_code == 404


def test_org_a_cannot_delete_org_b_alert(client, two_org_seed):
    _login(client, "user_a@orga.com", "passa123")
    alert_b_id = str(two_org_seed["alert_b"].id)
    response = client.delete(f"/api/alerts/{alert_b_id}")
    assert response.status_code == 404


def test_org_a_cannot_create_alert_on_org_b_device(client, two_org_seed):
    _login(client, "user_a@orga.com", "passa123")
    device_b_id = str(two_org_seed["device_b"].id)
    body = {
        "device_id": device_b_id,
        "metric": "temperature",
        "condition": "above",
        "threshold": 30.0,
        "notification_email": "hack@evil.com",
    }
    response = client.post("/api/alerts", json=body)
    assert response.status_code == 404
