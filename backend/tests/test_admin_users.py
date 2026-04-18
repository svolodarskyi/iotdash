"""Tests for admin user endpoints."""


def test_list_users(admin_client, seed_data):
    resp = admin_client.get("/api/admin/users")
    assert resp.status_code == 200
    users = resp.json()
    assert len(users) >= 1


def test_create_user(admin_client, seed_data):
    org_id = str(seed_data["org"].id)
    resp = admin_client.post("/api/admin/users", json={
        "email": "new@testorg.com",
        "password": "newpass123",
        "full_name": "New User",
        "organisation_id": org_id,
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["email"] == "new@testorg.com"
    assert data["full_name"] == "New User"
    assert data["role"] == "viewer"


def test_create_user_always_viewer(admin_client, seed_data):
    """Even if role is sent in the body, the user is always created as viewer."""
    org_id = str(seed_data["org"].id)
    resp = admin_client.post("/api/admin/users", json={
        "email": "sneaky@testorg.com",
        "password": "pass123",
        "full_name": "Sneaky User",
        "organisation_id": org_id,
    })
    assert resp.status_code == 201
    assert resp.json()["role"] == "viewer"


def test_create_user_duplicate_email(admin_client, seed_data, seed_admin):
    org_id = str(seed_data["org"].id)
    resp = admin_client.post("/api/admin/users", json={
        "email": "admin@testorg.com",
        "password": "dup123",
        "full_name": "Duplicate",
        "organisation_id": org_id,
    })
    assert resp.status_code == 409


def test_list_users_filter_by_org(admin_client, seed_data):
    org_id = str(seed_data["org"].id)
    resp = admin_client.get(f"/api/admin/users?org_id={org_id}")
    assert resp.status_code == 200
    users = resp.json()
    assert all(u["organisation_id"] == org_id for u in users)


def test_update_user(admin_client, seed_data, seed_admin):
    user_id = str(seed_data.get("admin_user", seed_admin).id if hasattr(seed_data, "admin_user") else seed_admin.id)
    resp = admin_client.put(f"/api/admin/users/{user_id}", json={"full_name": "Updated Admin"})
    assert resp.status_code == 200
    assert resp.json()["full_name"] == "Updated Admin"


def test_update_user_cannot_change_role(admin_client, seed_data):
    """Role field is not accepted in update — role stays unchanged."""
    org_id = str(seed_data["org"].id)
    create_resp = admin_client.post("/api/admin/users", json={
        "email": "roletest@testorg.com",
        "password": "pass123",
        "full_name": "Role Test",
        "organisation_id": org_id,
    })
    user_id = create_resp.json()["id"]
    resp = admin_client.put(f"/api/admin/users/{user_id}", json={"full_name": "Still Viewer"})
    assert resp.status_code == 200
    assert resp.json()["role"] == "viewer"


def test_deactivate_user(admin_client, seed_data):
    # Create a user first, then deactivate
    org_id = str(seed_data["org"].id)
    create_resp = admin_client.post("/api/admin/users", json={
        "email": "todeactivate@test.com",
        "password": "pass123",
        "full_name": "Deactivate Me",
        "organisation_id": org_id,
    })
    user_id = create_resp.json()["id"]
    resp = admin_client.delete(f"/api/admin/users/{user_id}")
    assert resp.status_code == 200


def test_viewer_cannot_create_user(auth_client, seed_data):
    org_id = str(seed_data["org"].id)
    resp = auth_client.post("/api/admin/users", json={
        "email": "x@x.com",
        "password": "x",
        "full_name": "X",
        "organisation_id": org_id,
    })
    assert resp.status_code == 403
