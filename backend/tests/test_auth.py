def test_login_success(client, seed_user):
    response = client.post(
        "/api/auth/login",
        json={"email": "testuser@testorg.com", "password": "testpass123"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["user"]["email"] == "testuser@testorg.com"
    assert "access_token" in response.cookies


def test_login_wrong_password(client, seed_user):
    response = client.post(
        "/api/auth/login",
        json={"email": "testuser@testorg.com", "password": "wrongpassword"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid email or password"


def test_login_nonexistent_user(client):
    response = client.post(
        "/api/auth/login",
        json={"email": "nobody@example.com", "password": "anything"},
    )
    assert response.status_code == 401


def test_me_authenticated(auth_client):
    response = auth_client.get("/api/auth/me")
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "testuser@testorg.com"
    assert data["full_name"] == "Test User"
    assert data["organisation_name"] == "Test Org"


def test_me_unauthenticated(client):
    response = client.get("/api/auth/me")
    assert response.status_code == 401


def test_logout(auth_client):
    response = auth_client.post("/api/auth/logout")
    assert response.status_code == 200
    # After logout, /me should return 401
    response = auth_client.get("/api/auth/me")
    assert response.status_code == 401


def test_login_inactive_user(client, db, seed_user):
    seed_user.is_active = False
    db.commit()
    response = client.post(
        "/api/auth/login",
        json={"email": "testuser@testorg.com", "password": "testpass123"},
    )
    assert response.status_code == 401
