import uuid


def test_list_organisations_empty(client):
    response = client.get("/api/organisations")
    assert response.status_code == 200
    assert response.json() == []


def test_list_organisations_with_data(client, seed_data):
    response = client.get("/api/organisations")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "Test Org"


def test_get_organisation(client, seed_data):
    org_id = str(seed_data["org"].id)
    response = client.get(f"/api/organisations/{org_id}")
    assert response.status_code == 200
    assert response.json()["name"] == "Test Org"


def test_get_organisation_not_found(client):
    fake_id = str(uuid.uuid4())
    response = client.get(f"/api/organisations/{fake_id}")
    assert response.status_code == 404
    assert response.json()["detail"] == "Organisation not found"


def test_list_org_devices(client, seed_data):
    org_id = str(seed_data["org"].id)
    response = client.get(f"/api/organisations/{org_id}/devices")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2


def test_list_org_devices_org_not_found(client):
    fake_id = str(uuid.uuid4())
    response = client.get(f"/api/organisations/{fake_id}/devices")
    assert response.status_code == 404
