import requests

BASE_URL = "http://localhost:8000"


def test_post_users():
    payload = {'name': 'Ryan', 'email': 'ryan@example.com', 'age': 25, 'active': True, 'tags': ['tester']}
    response = requests.post(f"{BASE_URL}/users", json=payload)
    assert response.status_code < 500
