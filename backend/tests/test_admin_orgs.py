"""Tests for admin organisation endpoints."""

import uuid


def test_list_orgs(admin_client, seed_data):
    resp = admin_client.get("/api/admin/organisations")
    assert resp.status_code == 200
    orgs = resp.json()
    assert len(orgs) >= 1
    assert any(o["name"] == "Test Org" for o in orgs)


def test_create_org(admin_client, seed_data, mock_grafana):
    mock_grafana.create_org.return_value = 99
    mock_grafana.create_dashboard_in_org.return_value = "new-dash-uid"
    resp = admin_client.post("/api/admin/organisations", json={"name": "New Corp"})
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "New Corp"
    assert data["grafana_org_id"] == 99
    assert "id" in data
    mock_grafana.create_org.assert_called_once_with("New Corp")
    mock_grafana.add_datasource_to_org.assert_called_once_with(99)


def test_create_org_duplicate_name(admin_client, seed_data):
    resp = admin_client.post("/api/admin/organisations", json={"name": "Test Org"})
    assert resp.status_code == 409


def test_update_org(admin_client, seed_data):
    org_id = str(seed_data["org"].id)
    resp = admin_client.put(f"/api/admin/organisations/{org_id}", json={"name": "Renamed Org"})
    assert resp.status_code == 200
    assert resp.json()["name"] == "Renamed Org"


def test_delete_org_with_devices_fails(admin_client, seed_data):
    org_id = str(seed_data["org"].id)
    resp = admin_client.delete(f"/api/admin/organisations/{org_id}")
    assert resp.status_code == 409


def test_delete_empty_org(admin_client, seed_data, mock_grafana):
    mock_grafana.create_org.return_value = 100
    mock_grafana.create_dashboard_in_org.return_value = "empty-dash-uid"
    # Create then delete an empty org
    create_resp = admin_client.post("/api/admin/organisations", json={"name": "Empty Org"})
    org_id = create_resp.json()["id"]
    resp = admin_client.delete(f"/api/admin/organisations/{org_id}")
    assert resp.status_code == 204


def test_viewer_cannot_access_admin_orgs(auth_client, seed_data):
    resp = auth_client.get("/api/admin/organisations")
    assert resp.status_code == 403
