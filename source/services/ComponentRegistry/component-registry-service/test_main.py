"""
Test suite for the Component Registry Service.

This module contains comprehensive tests for all CRUD operations and API endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import tempfile
import os

from main import app, get_db
from database import Base


# Create test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_component_registry.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Override database dependency for testing."""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

# Create test client
client = TestClient(app)


@pytest.fixture(scope="function")
def setup_database():
    """Setup test database for each test."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


class TestComponentRegistryEndpoints:
    """Test Component Registry endpoints."""

    def test_create_component_registry(self, setup_database):
        """Test creating a component registry."""
        registry_data = {
            "name": "test-registry",
            "url": "https://test-registry.example.com",
            "type": "upstream",
            "labels": {"environment": "test"}
        }
        response = client.post("/registries", json=registry_data)
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "test-registry"
        assert data["url"] == "https://test-registry.example.com"
        assert data["type"] == "upstream"
        assert data["labels"] == {"environment": "test"}

    def test_create_duplicate_registry(self, setup_database):
        """Test creating duplicate component registry should fail."""
        registry_data = {
            "name": "test-registry",
            "url": "https://test-registry.example.com",
            "type": "upstream"
        }
        # First creation should succeed
        response = client.post("/registries", json=registry_data)
        assert response.status_code == 200

        # Second creation should fail
        response = client.post("/registries", json=registry_data)
        assert response.status_code == 400
        assert "already exists" in response.json()["detail"]

    def test_get_component_registry(self, setup_database):
        """Test getting a component registry."""
        # Create registry first
        registry_data = {
            "name": "test-registry",
            "url": "https://test-registry.example.com",
            "type": "downstream"
        }
        client.post("/registries", json=registry_data)

        # Get registry
        response = client.get("/registries/test-registry")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "test-registry"
        assert data["type"] == "downstream"

    def test_get_nonexistent_registry(self, setup_database):
        """Test getting non-existent registry should return 404."""
        response = client.get("/registries/nonexistent")
        assert response.status_code == 404

    def test_get_all_registries(self, setup_database):
        """Test getting all registries."""
        # Create multiple registries
        registries = [
            {"name": "registry1", "url": "https://registry1.com", "type": "upstream"},
            {"name": "registry2", "url": "https://registry2.com", "type": "downstream"},
        ]
        for registry in registries:
            client.post("/registries", json=registry)

        response = client.get("/registries")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    def test_update_component_registry(self, setup_database):
        """Test updating a component registry."""
        # Create registry first
        registry_data = {
            "name": "test-registry",
            "url": "https://test-registry.example.com",
            "type": "upstream"
        }
        client.post("/registries", json=registry_data)

        # Update registry
        update_data = {
            "url": "https://updated-registry.example.com",
            "labels": {"environment": "production"}
        }
        response = client.put("/registries/test-registry", json=update_data)
        assert response.status_code == 200
        data = response.json()
        assert data["url"] == "https://updated-registry.example.com"
        assert data["labels"] == {"environment": "production"}

    def test_delete_component_registry(self, setup_database):
        """Test deleting a component registry."""
        # Create registry first
        registry_data = {
            "name": "test-registry",
            "url": "https://test-registry.example.com",
            "type": "upstream"
        }
        client.post("/registries", json=registry_data)

        # Delete registry
        response = client.delete("/registries/test-registry")
        assert response.status_code == 200

        # Verify deletion
        response = client.get("/registries/test-registry")
        assert response.status_code == 404


class TestComponentEndpoints:
    """Test Component endpoints."""

    @pytest.fixture(autouse=True)
    def setup_registry(self, setup_database):
        """Setup a test registry for component tests."""
        registry_data = {
            "name": "test-registry",
            "url": "https://test-registry.example.com",
            "type": "upstream"
        }
        client.post("/registries", json=registry_data)

    def test_create_component(self):
        """Test creating a component."""
        component_data = {
            "component_registry_ref": "test-registry",
            "component_name": "test-component",
            "exposed_apis": [
                {
                    "name": "test-api",
                    "oas_specification": "https://api.example.com/swagger.json",
                    "url": "https://api.example.com/v1",
                    "labels": {"version": "v1"}
                }
            ],
            "labels": {"team": "test-team"}
        }
        response = client.post("/components", json=component_data)
        assert response.status_code == 200
        data = response.json()
        assert data["component_name"] == "test-component"
        assert len(data["exposed_apis"]) == 1
        assert data["exposed_apis"][0]["name"] == "test-api"

    def test_create_component_nonexistent_registry(self, setup_database):
        """Test creating component with non-existent registry should fail."""
        component_data = {
            "component_registry_ref": "nonexistent-registry",
            "component_name": "test-component",
            "exposed_apis": [],
            "labels": {}
        }
        response = client.post("/components", json=component_data)
        assert response.status_code == 400
        assert "not found" in response.json()["detail"]

    def test_get_component(self):
        """Test getting a component."""
        # Create component first
        component_data = {
            "component_registry_ref": "test-registry",
            "component_name": "test-component",
            "exposed_apis": [],
            "labels": {"team": "test-team"}
        }
        client.post("/components", json=component_data)

        # Get component
        response = client.get("/components/test-registry/test-component")
        assert response.status_code == 200
        data = response.json()
        assert data["component_name"] == "test-component"
        assert data["component_registry_ref"] == "test-registry"

    def test_get_all_components(self):
        """Test getting all components."""
        # Create multiple components
        components = [
            {
                "component_registry_ref": "test-registry",
                "component_name": "component1",
                "exposed_apis": [],
                "labels": {}
            },
            {
                "component_registry_ref": "test-registry",
                "component_name": "component2",
                "exposed_apis": [],
                "labels": {}
            }
        ]
        for component in components:
            client.post("/components", json=component)

        response = client.get("/components")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    def test_update_component(self):
        """Test updating a component."""
        # Create component first
        component_data = {
            "component_registry_ref": "test-registry",
            "component_name": "test-component",
            "exposed_apis": [],
            "labels": {"team": "test-team"}
        }
        client.post("/components", json=component_data)

        # Update component
        update_data = {
            "exposed_apis": [
                {
                    "name": "new-api",
                    "oas_specification": "https://new-api.example.com/swagger.json",
                    "url": "https://new-api.example.com/v1",
                    "labels": {"version": "v1"}
                }
            ],
            "labels": {"team": "updated-team"}
        }
        response = client.put("/components/test-registry/test-component", json=update_data)
        assert response.status_code == 200
        data = response.json()
        assert len(data["exposed_apis"]) == 1
        assert data["labels"]["team"] == "updated-team"

    def test_delete_component(self):
        """Test deleting a component."""
        # Create component first
        component_data = {
            "component_registry_ref": "test-registry",
            "component_name": "test-component",
            "exposed_apis": [],
            "labels": {}
        }
        client.post("/components", json=component_data)

        # Delete component
        response = client.delete("/components/test-registry/test-component")
        assert response.status_code == 200

        # Verify deletion
        response = client.get("/components/test-registry/test-component")
        assert response.status_code == 404


class TestHealthAndUtilityEndpoints:
    """Test health check and utility endpoints."""

    def test_health_check(self, setup_database):
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    def test_root_endpoint(self, setup_database):
        """Test root endpoint."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "service" in data
        assert "Component Registry Service" in data["service"]


class TestQueryParameters:
    """Test query parameters and filtering."""

    @pytest.fixture(autouse=True)
    def setup_data(self, setup_database):
        """Setup test data."""
        # Create registry
        registry_data = {
            "name": "test-registry",
            "url": "https://test-registry.example.com",
            "type": "upstream"
        }
        client.post("/registries", json=registry_data)

    def test_pagination_registries(self):
        """Test pagination for registries."""
        # Create multiple registries
        for i in range(5):
            registry_data = {
                "name": f"registry-{i}",
                "url": f"https://registry-{i}.example.com",
                "type": "upstream"
            }
            client.post("/registries", json=registry_data)

        # Test pagination
        response = client.get("/registries?skip=2&limit=2")
        assert response.status_code == 200
        data = response.json()
        assert len(data) <= 2

    def test_filter_components_by_registry(self):
        """Test filtering components by registry."""
        # Create components
        component_data = {
            "component_registry_ref": "test-registry",
            "component_name": "test-component",
            "exposed_apis": [],
            "labels": {}
        }
        client.post("/components", json=component_data)

        # Filter by registry
        response = client.get("/components?registry_ref=test-registry")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["component_registry_ref"] == "test-registry"


if __name__ == "__main__":
    pytest.main([__file__])