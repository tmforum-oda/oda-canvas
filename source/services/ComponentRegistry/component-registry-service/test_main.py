"""
Test suite for the Component Registry Service.

This module contains comprehensive tests for all CRUD operations and API endpoints
following TM Forum ODA Canvas specification and BDD approach.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import tempfile
import os
import json

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


@pytest.fixture
def sample_registry_data():
    """Sample data for Component Registry tests."""
    return {
        "name": "test-registry",
        "url": "https://test-registry.example.com/api",
        "type": "upstream",
        "labels": {
            "environment": "test",
            "region": "us-west-1"
        }
    }


@pytest.fixture
def sample_component_data():
    """Sample data for Component tests."""
    return {
        "component_registry_ref": "test-registry",
        "component_name": "test-component",
        "component_version": "1.0.0",
        "description": "Test component for unit testing",
        "labels": {
            "category": "test",
            "owner": "test-team"
        }
    }


class TestHealthAndRoot:
    """Test health check and root endpoints."""

    def test_health_check(self, setup_database):
        """Test health check endpoint returns healthy status."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "component-registry-service"

    def test_root_endpoint_json(self, setup_database):
        """Test root endpoint returns service information."""
        response = client.get("/")
        # The root endpoint returns HTML, but we also have a JSON version
        # Let's test the actual behavior based on the implementation
        assert response.status_code == 200

    def test_components_gui_endpoint(self, setup_database):
        """Test components GUI endpoint returns HTML page."""
        response = client.get("/components-gui")
        assert response.status_code == 200
        assert "text/html" in response.headers.get("content-type", "")


class TestComponentRegistryEndpoints:
    """Test Component Registry CRUD endpoints."""

    def test_create_component_registry_success(self, setup_database, sample_registry_data):
        """Test successful creation of a component registry."""
        response = client.post("/registries", json=sample_registry_data)
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == sample_registry_data["name"]
        assert data["url"] == sample_registry_data["url"]
        assert data["type"] == sample_registry_data["type"]
        assert data["labels"] == sample_registry_data["labels"]

    def test_create_component_registry_duplicate_name(self, setup_database, sample_registry_data):
        """Test creation fails when registry name already exists."""
        # Create first registry
        client.post("/registries", json=sample_registry_data)
        
        # Try to create duplicate
        response = client.post("/registries", json=sample_registry_data)
        assert response.status_code == 400
        data = response.json()
        assert "already exists" in data["detail"]

    def test_create_component_registry_invalid_data(self, setup_database):
        """Test creation fails with invalid data."""
        invalid_data = {
            "name": "",  # Empty name should fail
            "url": "not-a-valid-url",
            "type": "invalid-type"
        }
        response = client.post("/registries", json=invalid_data)
        assert response.status_code == 422  # Validation error

    def test_get_all_component_registries(self, setup_database, sample_registry_data):
        """Test retrieving all component registries."""
        # Create test registry
        client.post("/registries", json=sample_registry_data)
        
        # Get all registries
        response = client.get("/registries")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["name"] == sample_registry_data["name"]

    def test_get_all_registries_with_pagination(self, setup_database):
        """Test pagination parameters for getting registries."""
        # Create multiple registries
        for i in range(5):
            registry_data = {
                "name": f"registry-{i}",
                "url": f"https://registry-{i}.example.com",
                "type": "upstream",
                "labels": {}
            }
            client.post("/registries", json=registry_data)
        
        # Test pagination
        response = client.get("/registries?skip=2&limit=2")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    def test_get_component_registry_by_name(self, setup_database, sample_registry_data):
        """Test retrieving specific component registry by name."""
        # Create registry
        client.post("/registries", json=sample_registry_data)
        
        # Get specific registry
        response = client.get(f"/registries/{sample_registry_data['name']}")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == sample_registry_data["name"]

    def test_get_component_registry_not_found(self, setup_database):
        """Test retrieving non-existent component registry."""
        response = client.get("/registries/non-existent")
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"]

    def test_update_component_registry(self, setup_database, sample_registry_data):
        """Test updating an existing component registry."""
        # Create registry
        client.post("/registries", json=sample_registry_data)
        
        # Update registry
        update_data = {
            "url": "https://updated-registry.example.com/api",
            "type": "downstream",
            "labels": {"updated": "true"}
        }
        response = client.put(f"/registries/{sample_registry_data['name']}", json=update_data)
        assert response.status_code == 200
        data = response.json()
        assert data["url"] == update_data["url"]
        assert data["type"] == update_data["type"]
        assert data["labels"]["updated"] == "true"

    def test_update_component_registry_not_found(self, setup_database):
        """Test updating non-existent component registry."""
        update_data = {"url": "https://new-url.example.com"}
        response = client.put("/registries/non-existent", json=update_data)
        assert response.status_code == 404

    def test_delete_component_registry(self, setup_database, sample_registry_data):
        """Test deleting a component registry."""
        # Create registry
        client.post("/registries", json=sample_registry_data)
        
        # Delete registry
        response = client.delete(f"/registries/{sample_registry_data['name']}")
        assert response.status_code == 200
        data = response.json()
        assert "deleted successfully" in data["message"]
        
        # Verify deletion
        response = client.get(f"/registries/{sample_registry_data['name']}")
        assert response.status_code == 404

    def test_delete_component_registry_not_found(self, setup_database):
        """Test deleting non-existent component registry."""
        response = client.delete("/registries/non-existent")
        assert response.status_code == 404


class TestComponentEndpoints:
    """Test Component CRUD endpoints."""

    def test_create_component_success(self, setup_database, sample_registry_data, sample_component_data):
        """Test successful creation of a component."""
        # First create registry
        client.post("/registries", json=sample_registry_data)
        
        # Create component
        response = client.post("/components", json=sample_component_data)
        assert response.status_code == 200
        data = response.json()
        assert data["component_name"] == sample_component_data["component_name"]
        assert data["component_registry_ref"] == sample_component_data["component_registry_ref"]

    def test_create_component_duplicate(self, setup_database, sample_registry_data, sample_component_data):
        """Test creation fails when component already exists."""
        # Create registry and component
        client.post("/registries", json=sample_registry_data)
        client.post("/components", json=sample_component_data)
        
        # Try to create duplicate
        response = client.post("/components", json=sample_component_data)
        assert response.status_code == 400
        assert "already exists" in response.json()["detail"]

    def test_create_component_invalid_registry(self, setup_database, sample_component_data):
        """Test creation fails with non-existent registry reference."""
        response = client.post("/components", json=sample_component_data)
        assert response.status_code == 400

    def test_get_all_components(self, setup_database, sample_registry_data, sample_component_data):
        """Test retrieving all components."""
        # Setup
        client.post("/registries", json=sample_registry_data)
        client.post("/components", json=sample_component_data)
        
        # Get all components
        response = client.get("/components")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1

    def test_get_components_by_registry(self, setup_database, sample_registry_data, sample_component_data):
        """Test retrieving components filtered by registry."""
        # Setup
        client.post("/registries", json=sample_registry_data)
        client.post("/components", json=sample_component_data)
        
        # Get components by registry
        response = client.get(f"/components?registry_ref={sample_registry_data['name']}")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["component_registry_ref"] == sample_registry_data["name"]

    def test_get_component_by_registry_and_name(self, setup_database, sample_registry_data, sample_component_data):
        """Test retrieving specific component by registry and name."""
        # Setup
        client.post("/registries", json=sample_registry_data)
        client.post("/components", json=sample_component_data)
        
        # Get specific component
        response = client.get(f"/components/{sample_component_data['component_registry_ref']}/{sample_component_data['component_name']}")
        assert response.status_code == 200
        data = response.json()
        assert data["component_name"] == sample_component_data["component_name"]

    def test_get_component_not_found(self, setup_database):
        """Test retrieving non-existent component."""
        response = client.get("/components/non-existent-registry/non-existent-component")
        assert response.status_code == 404

    def test_update_component(self, setup_database, sample_registry_data, sample_component_data):
        """Test updating an existing component."""
        # Setup
        client.post("/registries", json=sample_registry_data)
        client.post("/components", json=sample_component_data)
        
        # Update component
        update_data = {
            "component_version": "2.0.0",
            "description": "Updated test component",
            "labels": {"updated": "true"}
        }
        response = client.put(
            f"/components/{sample_component_data['component_registry_ref']}/{sample_component_data['component_name']}",
            json=update_data
        )
        assert response.status_code == 200
        data = response.json()
        assert data["component_version"] == update_data["component_version"]
        assert data["description"] == update_data["description"]

    def test_update_component_not_found(self, setup_database):
        """Test updating non-existent component."""
        update_data = {"component_version": "2.0.0"}
        response = client.put("/components/non-existent/non-existent", json=update_data)
        assert response.status_code == 404

    def test_delete_component(self, setup_database, sample_registry_data, sample_component_data):
        """Test deleting a component."""
        # Setup
        client.post("/registries", json=sample_registry_data)
        client.post("/components", json=sample_component_data)
        
        # Delete component
        response = client.delete(f"/components/{sample_component_data['component_registry_ref']}/{sample_component_data['component_name']}")
        assert response.status_code == 200
        assert "deleted successfully" in response.json()["message"]
        
        # Verify deletion
        response = client.get(f"/components/{sample_component_data['component_registry_ref']}/{sample_component_data['component_name']}")
        assert response.status_code == 404

    def test_delete_component_not_found(self, setup_database):
        """Test deleting non-existent component."""
        response = client.delete("/components/non-existent/non-existent")
        assert response.status_code == 404


class TestRegistryComponentsEndpoint:
    """Test the utility endpoint for getting components by registry."""

    def test_get_registry_components(self, setup_database, sample_registry_data, sample_component_data):
        """Test retrieving all components for a specific registry."""
        # Setup
        client.post("/registries", json=sample_registry_data)
        client.post("/components", json=sample_component_data)
        
        # Get registry components
        response = client.get(f"/registries/{sample_registry_data['name']}/components")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["component_registry_ref"] == sample_registry_data["name"]

    def test_get_registry_components_registry_not_found(self, setup_database):
        """Test retrieving components for non-existent registry."""
        response = client.get("/registries/non-existent/components")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

    def test_get_registry_components_empty(self, setup_database, sample_registry_data):
        """Test retrieving components for registry with no components."""
        # Create registry but no components
        client.post("/registries", json=sample_registry_data)
        
        response = client.get(f"/registries/{sample_registry_data['name']}/components")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0


class TestValidationAndEdgeCases:
    """Test validation rules and edge cases."""

    def test_registry_name_validation(self, setup_database):
        """Test registry name validation rules."""
        # Test empty name
        invalid_data = {
            "name": "",
            "url": "https://example.com",
            "type": "upstream"
        }
        response = client.post("/registries", json=invalid_data)
        assert response.status_code == 422

    def test_invalid_registry_type(self, setup_database):
        """Test invalid registry type."""
        invalid_data = {
            "name": "test-registry",
            "url": "https://example.com",
            "type": "invalid-type"
        }
        response = client.post("/registries", json=invalid_data)
        assert response.status_code == 422

    def test_component_name_validation(self, setup_database, sample_registry_data):
        """Test component name validation."""
        client.post("/registries", json=sample_registry_data)
        
        invalid_component = {
            "component_registry_ref": sample_registry_data["name"],
            "component_name": "",  # Empty name
            "component_version": "1.0.0"
        }
        response = client.post("/components", json=invalid_component)
        assert response.status_code == 422

    def test_pagination_limits(self, setup_database):
        """Test pagination parameter limits."""
        # Test invalid skip parameter
        response = client.get("/registries?skip=-1")
        assert response.status_code == 422

        # Test invalid limit parameter
        response = client.get("/registries?limit=0")
        assert response.status_code == 422

        response = client.get("/registries?limit=10000")
        assert response.status_code == 422

    def test_special_characters_in_names(self, setup_database):
        """Test handling of special characters in names."""
        registry_data = {
            "name": "test-registry-with-special_chars.123",
            "url": "https://example.com",
            "type": "upstream"
        }
        response = client.post("/registries", json=registry_data)
        assert response.status_code == 200

    def test_large_labels_object(self, setup_database):
        """Test handling of large labels objects."""
        large_labels = {f"key{i}": f"value{i}" for i in range(100)}
        registry_data = {
            "name": "test-registry-large-labels",
            "url": "https://example.com",
            "type": "upstream",
            "labels": large_labels
        }
        response = client.post("/registries", json=registry_data)
        assert response.status_code == 200


class TestIntegrationScenarios:
    """Test realistic integration scenarios."""

    def test_full_workflow_scenario(self, setup_database):
        """Test a complete workflow: create registry, add components, update, delete."""
        # Step 1: Create registry
        registry_data = {
            "name": "production-registry",
            "url": "https://prod-registry.company.com/api",
            "type": "upstream",
            "labels": {
                "environment": "production",
                "owner": "platform-team"
            }
        }
        response = client.post("/registries", json=registry_data)
        assert response.status_code == 200

        # Step 2: Add multiple components
        components = [
            {
                "component_registry_ref": "production-registry",
                "component_name": "user-service",
                "component_version": "1.0.0",
                "description": "User management service"
            },
            {
                "component_registry_ref": "production-registry",
                "component_name": "billing-service",
                "component_version": "2.1.0",
                "description": "Billing and payment service"
            }
        ]
        
        for component in components:
            response = client.post("/components", json=component)
            assert response.status_code == 200

        # Step 3: Verify components are listed
        response = client.get("/registries/production-registry/components")
        assert response.status_code == 200
        assert len(response.json()) == 2

        # Step 4: Update a component
        update_data = {
            "component_version": "1.1.0",
            "description": "Updated user management service with new features"
        }
        response = client.put("/components/production-registry/user-service", json=update_data)
        assert response.status_code == 200
        assert response.json()["component_version"] == "1.1.0"

        # Step 5: Delete a component
        response = client.delete("/components/production-registry/billing-service")
        assert response.status_code == 200

        # Step 6: Verify only one component remains
        response = client.get("/registries/production-registry/components")
        assert response.status_code == 200
        assert len(response.json()) == 1

    def test_multiple_registries_scenario(self, setup_database):
        """Test scenario with multiple registries and cross-registry operations."""
        # Create multiple registries
        registries = [
            {
                "name": "dev-registry",
                "url": "https://dev.company.com/api",
                "type": "self",
                "labels": {"env": "development"}
            },
            {
                "name": "staging-registry",
                "url": "https://staging.company.com/api",
                "type": "upstream",
                "labels": {"env": "staging"}
            }
        ]
        
        for registry in registries:
            response = client.post("/registries", json=registry)
            assert response.status_code == 200

        # Add components to different registries
        dev_component = {
            "component_registry_ref": "dev-registry",
            "component_name": "test-service",
            "component_version": "0.1.0"
        }
        staging_component = {
            "component_registry_ref": "staging-registry", 
            "component_name": "test-service",
            "component_version": "1.0.0"
        }
        
        client.post("/components", json=dev_component)
        client.post("/components", json=staging_component)

        # Verify components are in correct registries
        dev_response = client.get("/components?registry_ref=dev-registry")
        staging_response = client.get("/components?registry_ref=staging-registry")
        
        assert len(dev_response.json()) == 1
        assert len(staging_response.json()) == 1
        assert dev_response.json()[0]["component_version"] == "0.1.0"
        assert staging_response.json()[0]["component_version"] == "1.0.0"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])