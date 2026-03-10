import requests

BASE_URL = "http://localhost:8000"


def test_get_users():
    response = requests.get(f"{BASE_URL}/users")
    assert response.status_code < 500


def test_post_users():
    response = requests.post(f"{BASE_URL}/users")
    assert response.status_code < 500


def test_delete_users_id():
    response = requests.delete(f"{BASE_URL}/users/1")
    assert response.status_code < 500
