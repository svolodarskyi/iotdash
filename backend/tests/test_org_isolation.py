def _login(client, email, password):
    resp = client.post("/api/auth/login", json={"email": email, "password": password})
    assert resp.status_code == 200
    return client


def test_org_a_sees_only_own_devices(client, two_org_seed):
    _login(client, "user_a@orga.com", "passa123")
    response = client.get("/api/devices")
    assert response.status_code == 200
    devices = response.json()
    assert len(devices) == 1
    assert devices[0]["device_code"] == "org_a_sensor"


def test_org_b_sees_only_own_devices(client, two_org_seed):
    _login(client, "user_b@orgb.com", "passb123")
    response = client.get("/api/devices")
    assert response.status_code == 200
    devices = response.json()
    assert len(devices) == 1
    assert devices[0]["device_code"] == "org_b_sensor"


def test_org_b_cannot_access_org_a_device(client, two_org_seed):
    _login(client, "user_b@orgb.com", "passb123")
    device_a_id = str(two_org_seed["device_a"].id)
    response = client.get(f"/api/devices/{device_a_id}")
    assert response.status_code == 404


def test_org_a_cannot_access_org_b_device(client, two_org_seed):
    _login(client, "user_a@orga.com", "passa123")
    device_b_id = str(two_org_seed["device_b"].id)
    response = client.get(f"/api/devices/{device_b_id}")
    assert response.status_code == 404


def test_org_b_cannot_access_org_a_embed_urls(client, two_org_seed):
    _login(client, "user_b@orgb.com", "passb123")
    device_a_id = str(two_org_seed["device_a"].id)
    response = client.get(f"/api/devices/{device_a_id}/embed-urls")
    assert response.status_code == 404


def test_org_a_sees_only_own_organisation(client, two_org_seed):
    _login(client, "user_a@orga.com", "passa123")
    response = client.get("/api/organisations")
    assert response.status_code == 200
    orgs = response.json()
    assert len(orgs) == 1
    assert orgs[0]["name"] == "Org A"


def test_org_a_cannot_access_org_b_details(client, two_org_seed):
    _login(client, "user_a@orga.com", "passa123")
    org_b_id = str(two_org_seed["org_b"].id)
    response = client.get(f"/api/organisations/{org_b_id}")
    assert response.status_code == 404
