import requests
import jsonschema

BASE_URL = "http://localhost:8000"


def test_post_users():
    payload = {'name': 'Ryan', 'email': 'ryan@example.com', 'age': 25, 'role': 'admin'}
    response = requests.post(f"{BASE_URL}/users", json=payload)
    assert response.status_code == 201
    data = response.json()
    schema = {'type': 'object', 'required': ['id', 'name', 'email'], 'properties': {'id': {'type': 'integer'}, 'name': {'type': 'string'}, 'email': {'type': 'string'}}}
    jsonschema.validate(data, schema)


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
