from openapi_test_generator.parser import extract_endpoints


def test_extract_endpoints_returns_methods_and_paths() -> None:
    spec = {
        "paths": {
            "/users": {
                "get": {"summary": "List users"},
                "post": {"summary": "Create user"},
            }
        }
    }

    endpoints = extract_endpoints(spec)

    assert endpoints == [
        ("GET", "/users", {"summary": "List users", "parameters": []}),
        ("POST", "/users", {"summary": "Create user", "parameters": []}),
    ]


def test_extract_endpoints_ignores_non_http_keys() -> None:
    spec = {
        "paths": {
            "/users": {
                "parameters": [],
                "get": {"summary": "List users"},
            }
        }
    }

    endpoints = extract_endpoints(spec)

    assert endpoints == [
        ("GET", "/users", {"summary": "List users", "parameters": []}),
    ]


def test_extract_endpoints_merges_path_level_parameters() -> None:
    spec = {
        "paths": {
            "/users/{id}": {
                "parameters": [
                    {
                        "name": "id",
                        "in": "path",
                        "required": True,
                        "schema": {"type": "integer"},
                    }
                ],
                "get": {"summary": "Get user"},
            }
        }
    }

    endpoints = extract_endpoints(spec)

    assert endpoints == [
        (
            "GET",
            "/users/{id}",
            {
                "summary": "Get user",
                "parameters": [
                    {
                        "name": "id",
                        "in": "path",
                        "required": True,
                        "schema": {"type": "integer"},
                    }
                ],
            },
        )
    ]


def test_extract_endpoints_filters_by_single_method() -> None:
    spec = {
        "paths": {
            "/users": {
                "get": {"summary": "List users"},
                "post": {"summary": "Create user"},
            }
        }
    }

    endpoints = extract_endpoints(spec, selected_methods={"GET"})

    assert endpoints == [
        ("GET", "/users", {"summary": "List users", "parameters": []})
    ]


def test_extract_endpoints_filters_by_multiple_methods() -> None:
    spec = {
        "paths": {
            "/users": {
                "get": {"summary": "List users"},
                "post": {"summary": "Create user"},
                "delete": {"summary": "Delete users"},
            }
        }
    }

    endpoints = extract_endpoints(spec, selected_methods={"GET", "POST"})

    assert endpoints == [
        ("GET", "/users", {"summary": "List users", "parameters": []}),
        ("POST", "/users", {"summary": "Create user", "parameters": []}),
    ]


def test_extract_endpoints_returns_all_methods_when_no_filter_provided() -> None:
    spec = {
        "paths": {
            "/users": {
                "get": {"summary": "List users"},
                "post": {"summary": "Create user"},
            }
        }
    }

    endpoints = extract_endpoints(spec)

    assert endpoints == [
        ("GET", "/users", {"summary": "List users", "parameters": []}),
        ("POST", "/users", {"summary": "Create user", "parameters": []}),
    ]


def test_extract_endpoints_filters_by_tag() -> None:
    spec = {
        "paths": {
            "/users": {
                "get": {"summary": "List users", "tags": ["Users"]},
                "post": {"summary": "Create user", "tags": ["Admin"]},
            }
        }
    }

    endpoints = extract_endpoints(spec, selected_tags={"Users"})

    assert endpoints == [
        ("GET", "/users", {"summary": "List users", "tags": ["Users"], "parameters": []})
    ]


def test_extract_endpoints_filters_by_multiple_tags() -> None:
    spec = {
        "paths": {
            "/users": {
                "get": {"summary": "List users", "tags": ["Users"]},
                "post": {"summary": "Create user", "tags": ["Admin"]},
                "delete": {"summary": "Delete user", "tags": ["Dangerous"]},
            }
        }
    }

    endpoints = extract_endpoints(spec, selected_tags={"Users", "Admin"})

    assert endpoints == [
        ("GET", "/users", {"summary": "List users", "tags": ["Users"], "parameters": []}),
        ("POST", "/users", {"summary": "Create user", "tags": ["Admin"], "parameters": []}),
    ]


def test_extract_endpoints_filters_by_single_tag() -> None:
    spec = {
        "paths": {
            "/users": {
                "get": {
                    "tags": ["Users"]
                }
            },
            "/login": {
                "post": {
                    "tags": ["Auth"]
                }
            },
        }
    }

    endpoints = extract_endpoints(spec, selected_tags={"Users"})

    assert endpoints == [
        ("GET", "/users", {"tags": ["Users"], "parameters": []})
    ]


def test_extract_endpoints_filters_by_multiple_tags() -> None:
    spec = {
        "paths": {
            "/users": {
                "get": {
                    "tags": ["Users"]
                }
            },
            "/login": {
                "post": {
                    "tags": ["Auth"]
                }
            },
            "/health": {
                "get": {
                    "tags": ["System"]
                }
            },
        }
    }

    endpoints = extract_endpoints(spec, selected_tags={"Users", "Auth"})

    assert len(endpoints) == 2


def test_extract_endpoints_returns_no_matches_for_unknown_tag() -> None:
    spec = {
        "paths": {
            "/users": {
                "get": {
                    "tags": ["Users"]
                }
            }
        }
    }

    endpoints = extract_endpoints(spec, selected_tags={"DoesNotExist"})

    assert endpoints == []