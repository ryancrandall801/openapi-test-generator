import requests

BASE_URL = "http://localhost:8000"


def test_post_users():
    payload = {'name': 'Ryan', 'email': 'ryan@example.com', 'age': 25, 'role': 'admin'}
    response = requests.post(f"{BASE_URL}/users", json=payload)
    assert response.status_code < 500


def test_post_users_missing_name():
    payload = {'email': 'ryan@example.com', 'age': 25, 'role': 'admin'}
    response = requests.post(f"{BASE_URL}/users", json=payload)
    assert response.status_code >= 400


def test_post_users_missing_email():
    payload = {'name': 'Ryan', 'age': 25, 'role': 'admin'}
    response = requests.post(f"{BASE_URL}/users", json=payload)
    assert response.status_code >= 400


def test_post_users_invalid_role_enum():
    payload = {'name': 'Ryan', 'email': 'ryan@example.com', 'age': 25, 'role': 'invalid_enum_value'}
    response = requests.post(f"{BASE_URL}/users", json=payload)
    assert response.status_code >= 400
