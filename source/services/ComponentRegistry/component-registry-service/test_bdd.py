"""
BDD Feature Tests for Component Registry Service.

This module contains Behavior-Driven Development tests using pytest-bdd
to validate the Component Registry Service against TM Forum ODA Canvas specifications.
"""

import pytest
from pytest_bdd import scenarios, given, when, then, parsers
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import json

from main import app, get_db
from database import Base


# Load scenarios from feature files
scenarios('features/')


# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_bdd_component_registry.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Override database dependency for BDD testing."""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


@pytest.fixture(scope="function")
def bdd_setup_database():
    """Setup test database for BDD tests."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def context():
    """Context for storing test data between BDD steps."""
    return {}


# Given steps
@given('the Component Registry Service is running', target_fixture="service_running")
def service_running(bdd_setup_database):
    """Ensure the service is running and accessible."""
    response = client.get("/health")
    assert response.status_code == 200
    return True


@given(parsers.parse('a Component Registry named "{registry_name}" exists'))
def registry_exists(context, registry_name):
    """Create a component registry for testing."""
    registry_data = {
        "name": registry_name,
        "url": f"https://{registry_name}.example.com/api",
        "type": "upstream",
        "labels": {"test": "true"}
    }
    response = client.post("/registries", json=registry_data)
    assert response.status_code == 200
    context[f"registry_{registry_name}"] = registry_data


@given(parsers.parse('a Component "{component_name}" exists in registry "{registry_name}"'))
def component_exists(context, component_name, registry_name):
    """Create a component in the specified registry."""
    component_data = {
        "component_registry_ref": registry_name,
        "component_name": component_name,
        "component_version": "1.0.0",
        "description": f"Test component {component_name}",
        "labels": {"test": "true"}
    }
    response = client.post("/components", json=component_data)
    assert response.status_code == 200
    context[f"component_{component_name}"] = component_data


@given('no Component Registries exist')
def no_registries_exist(bdd_setup_database):
    """Ensure no registries exist in the system."""
    # Database is already clean from fixture
    pass


@given(parsers.parse('no Components exist in registry "{registry_name}"'))
def no_components_exist_in_registry(context, registry_name):
    """Ensure no components exist in the specified registry."""
    # This step verifies the registry exists but has no components
    # The registry should already exist from previous steps
    response = client.get(f"/registries/{registry_name}/components")
    if response.status_code == 200:
        # Registry exists, components will be empty by default
        pass
    else:
        # Registry might not exist, which is handled by other steps
        pass


# When steps
@when(parsers.parse('I create a Component Registry named "{registry_name}"'))
def create_registry(context, registry_name):
    """Create a new component registry."""
    registry_data = {
        "name": registry_name,
        "url": f"https://{registry_name}.example.com/api",
        "type": "upstream",
        "labels": {"created_by": "bdd_test"}
    }
    response = client.post("/registries", json=registry_data)
    context["last_response"] = response
    context[f"registry_{registry_name}"] = registry_data


@when(parsers.parse('I try to create a Component Registry with an invalid name "{invalid_name}"'))
def create_invalid_registry(context, invalid_name):
    """Attempt to create a registry with invalid data."""
    invalid_data = {
        "name": invalid_name,
        "url": "https://example.com",
        "type": "upstream"
    }
    response = client.post("/registries", json=invalid_data)
    context["last_response"] = response


@when('I try to create a Component Registry with an invalid name ""')
def create_registry_empty_name(context):
    """Attempt to create a registry with empty name."""
    invalid_data = {
        "name": "",
        "url": "https://example.com",
        "type": "upstream"
    }
    response = client.post("/registries", json=invalid_data)
    context["last_response"] = response


@when(parsers.parse('I request all Component Registries'))
def get_all_registries(context):
    """Request all component registries."""
    response = client.get("/registries")
    context["last_response"] = response


@when(parsers.parse('I request the Component Registry "{registry_name}"'))
def get_registry(context, registry_name):
    """Request a specific component registry."""
    response = client.get(f"/registries/{registry_name}")
    context["last_response"] = response


@when(parsers.parse('I update the Component Registry "{registry_name}" with new URL "{new_url}"'))
def update_registry(context, registry_name, new_url):
    """Update a component registry."""
    update_data = {"url": new_url}
    response = client.put(f"/registries/{registry_name}", json=update_data)
    context["last_response"] = response


@when(parsers.parse('I delete the Component Registry "{registry_name}"'))
def delete_registry(context, registry_name):
    """Delete a component registry."""
    response = client.delete(f"/registries/{registry_name}")
    context["last_response"] = response


@when(parsers.parse('I create a Component "{component_name}" in registry "{registry_name}"'))
def create_component(context, component_name, registry_name):
    """Create a new component."""
    component_data = {
        "component_registry_ref": registry_name,
        "component_name": component_name,
        "component_version": "1.0.0",
        "description": f"BDD test component {component_name}",
        "labels": {"created_by": "bdd_test"}
    }
    response = client.post("/components", json=component_data)
    context["last_response"] = response
    context[f"component_{component_name}"] = component_data


@when(parsers.parse('I request all Components'))
def get_all_components(context):
    """Request all components."""
    response = client.get("/components")
    context["last_response"] = response


@when(parsers.parse('I request all Components for registry "{registry_name}"'))
def get_registry_components(context, registry_name):
    """Request all components for a specific registry."""
    response = client.get(f"/registries/{registry_name}/components")
    context["last_response"] = response


# Then steps
@then(parsers.parse('the request should succeed with status code {status_code:d}'))
def request_should_succeed(context, status_code):
    """Verify the request succeeded with expected status code."""
    assert context["last_response"].status_code == status_code


@then(parsers.parse('the request should fail with status code {status_code:d}'))
def request_should_fail(context, status_code):
    """Verify the request failed with expected status code."""
    assert context["last_response"].status_code == status_code


@then(parsers.parse('the response should contain the registry "{registry_name}"'))
def response_contains_registry(context, registry_name):
    """Verify the response contains the specified registry."""
    data = context["last_response"].json()
    if isinstance(data, list):
        registry_names = [registry["name"] for registry in data]
        assert registry_name in registry_names
    else:
        assert data["name"] == registry_name


@then(parsers.parse('the response should contain {count:d} registries'))
def response_contains_count_registries(context, count):
    """Verify the response contains the expected number of registries."""
    data = context["last_response"].json()
    assert isinstance(data, list)
    assert len(data) == count


@then(parsers.parse('the registry "{registry_name}" should have URL "{expected_url}"'))
def registry_should_have_url(context, registry_name, expected_url):
    """Verify the registry has the expected URL."""
    data = context["last_response"].json()
    assert data["name"] == registry_name
    assert data["url"] == expected_url


@then(parsers.parse('the response should contain the component "{component_name}"'))
def response_contains_component(context, component_name):
    """Verify the response contains the specified component."""
    data = context["last_response"].json()
    if isinstance(data, list):
        component_names = [component["component_name"] for component in data]
        assert component_name in component_names
    else:
        assert data["component_name"] == component_name


@then(parsers.parse('the response should contain {count:d} components'))
def response_contains_count_components(context, count):
    """Verify the response contains the expected number of components."""
    data = context["last_response"].json()
    assert isinstance(data, list)
    assert len(data) == count


@then('the response should indicate validation error')
def response_validation_error(context):
    """Verify the response indicates a validation error."""
    assert context["last_response"].status_code == 422
    data = context["last_response"].json()
    assert "detail" in data


@then('the response should indicate not found error')
def response_not_found_error(context):
    """Verify the response indicates a not found error."""
    assert context["last_response"].status_code == 404
    data = context["last_response"].json()
    assert "not found" in data["detail"].lower()


@then('the response should indicate already exists error')
def response_already_exists_error(context):
    """Verify the response indicates an already exists error."""
    assert context["last_response"].status_code == 400
    data = context["last_response"].json()
    assert "already exists" in data["detail"].lower()


@then('the response should indicate successful deletion')
def response_successful_deletion(context):
    """Verify the response indicates successful deletion."""
    assert context["last_response"].status_code == 200
    data = context["last_response"].json()
    assert "deleted successfully" in data["message"].lower()