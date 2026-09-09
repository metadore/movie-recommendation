import pytest
from fastapi.testclient import TestClient

from main import app


@pytest.fixture()
def client():
    with TestClient(app) as c:
        yield c


def test_health(client):
    res = client.get("/api/health")
    assert res.status_code == 200
    assert res.json()["message"] == "Backend running"


def test_movies_list(client):
    res = client.get("/api/movies")
    assert res.status_code == 200
    assert isinstance(res.json(), list)


def test_auth_and_favourites_flow(client):
    username = "test_user_cinepulse"
    password = "testpass"

    client.post("/api/auth/register", json={"username": username, "password": password})
    login = client.post(
        "/api/auth/login", json={"username": username, "password": password}
    )
    assert login.status_code == 200
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    movies = client.get("/api/movies").json()
    assert movies, "Seed movies before running tests (python add_movies.py)"
    movie_id = movies[0]["id"]

    add = client.post(f"/api/favourites/{movie_id}", headers=headers)
    assert add.status_code == 200

    favs = client.get("/api/favourites", headers=headers)
    assert favs.status_code == 200
    assert any(m["id"] == movie_id for m in favs.json())

    remove = client.delete(f"/api/favourites/{movie_id}", headers=headers)
    assert remove.status_code == 200


def test_recommend(client):
    res = client.get("/api/recommend", params={"movie": "Inception"})
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
    assert data
    assert "title" in data[0]
    assert "reason" in data[0]


def test_search_and_filter(client):
    search = client.get("/api/movies/search", params={"title": "dark"})
    assert search.status_code == 200
    filt = client.get("/api/movies/filter", params={"genre": "Action"})
    assert filt.status_code == 200
