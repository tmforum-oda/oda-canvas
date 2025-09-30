#!/usr/bin/env python3
"""
Unit tests for the ODA Component Kubernetes to Registry Sync Tool.

Tests cover component transformation, registry client operations, and integration scenarios.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import json
from datetime import datetime

from k8s_component_sync import (
    ComponentTransformer, 
    RegistryClient, 
    RegistryConfig, 
    KubernetesComponentReader,
    ComponentSyncTool,
    SyncConfig
)


class TestComponentTransformer(unittest.TestCase):
    """Test the ComponentTransformer class."""
    
    def setUp(self):
        self.transformer = ComponentTransformer()
        self.sample_k8s_component = {
            "metadata": {
                "name": "demo-productcatalog",
                "namespace": "components",
                "labels": {
                    "app.kubernetes.io/managed-by": "Helm",
                    "oda.tmforum.org/componentName": "productcatalog"
                }
            },
            "spec": {
                "version": "0.0.1",
                "description": "Product Catalog ODA Component",
                "functionalBlock": "CoreCommerce",
                "id": "TMFC001",
                "status": "specified",
                "coreFunction": {
                    "exposedAPIs": [{
                        "name": "productcatalogmanagement",
                        "apiType": "openapi",
                        "path": "/tmf-api/productCatalogManagement/v4",
                        "port": 8080,
                        "implementation": "prodcat-api",
                        "specification": [
                            "https://raw.githubusercontent.com/tmforum-apis/TMF620_ProductCatalog/master/TMF620-ProductCatalog-v4.0.0.swagger.json"
                        ]
                    }]
                },
                "managementFunction": {
                    "exposedAPIs": [{
                        "name": "metrics",
                        "apiType": "prometheus", 
                        "path": "/metrics",
                        "port": 4000,
                        "implementation": "prodcat-sm"
                    }]
                }
            }
        }
    
    def test_transform_component_basic(self):
        """Test basic component transformation."""
        result = self.transformer.transform_component(self.sample_k8s_component, "test-registry")
        
        self.assertEqual(result['component_registry_ref'], "test-registry")
        self.assertEqual(result['component_name'], "demo-productcatalog")
        self.assertEqual(result['component_version'], "0.0.1")
        self.assertEqual(result['description'], "Product Catalog ODA Component")
        
        # Check labels
        self.assertIn('functionalBlock', result['labels'])
        self.assertEqual(result['labels']['functionalBlock'], 'CoreCommerce')
        self.assertIn('syncedFrom', result['labels'])
        self.assertEqual(result['labels']['syncedFrom'], 'kubernetes')
    
    def test_transform_exposed_apis(self):
        """Test exposed API transformation."""
        result = self.transformer.transform_component(self.sample_k8s_component, "test-registry")
        
        # Should have 2 APIs (core + management)
        self.assertEqual(len(result['exposed_apis']), 2)
        
        # Check core API
        core_api = next(api for api in result['exposed_apis'] if 'productcatalogmanagement' in api['name'])
        self.assertEqual(core_api['name'], "demo-productcatalog-productcatalogmanagement")
        self.assertIn('swagger.json', core_api['oas_specification'])
        self.assertEqual(core_api['url'], "http://prodcat-api:8080/tmf-api/productCatalogManagement/v4")
        
        # Check management API
        mgmt_api = next(api for api in result['exposed_apis'] if 'metrics' in api['name'])
        self.assertEqual(mgmt_api['labels']['componentType'], 'management')
    
    def test_transform_component_minimal(self):
        """Test transformation with minimal component data."""
        minimal_component = {
            "metadata": {"name": "minimal-component"},
            "spec": {}
        }
        
        result = self.transformer.transform_component(minimal_component, "test-registry")
        
        self.assertEqual(result['component_name'], "minimal-component")
        self.assertEqual(result['component_version'], "1.0.0")  # Default version
        self.assertEqual(len(result['exposed_apis']), 0)


class TestRegistryClient(unittest.TestCase):
    """Test the RegistryClient class."""
    
    def setUp(self):
        config = RegistryConfig(url="http://test-registry")
        self.client = RegistryClient(config)
    
    @patch('requests.Session.get')
    @patch('requests.Session.post')
    def test_create_registry_new(self, mock_post, mock_get):
        """Test creating a new registry."""
        # Registry doesn't exist
        mock_get.return_value.status_code = 404
        # Registry creation succeeds
        mock_post.return_value.status_code = 200
        
        result = self.client.create_registry("new-registry", "Test registry")
        
        self.assertTrue(result)
        mock_get.assert_called_once()
        mock_post.assert_called_once()
    
    @patch('requests.Session.get')
    def test_create_registry_existing(self, mock_get):
        """Test when registry already exists."""
        mock_get.return_value.status_code = 200
        
        result = self.client.create_registry("existing-registry")
        
        self.assertTrue(result)
        mock_get.assert_called_once()
    
    @patch('requests.Session.get')
    @patch('requests.Session.post')
    def test_sync_component_new(self, mock_post, mock_get):
        """Test syncing a new component."""
        component_data = {
            'component_registry_ref': 'test-registry',
            'component_name': 'test-component',
            'component_version': '1.0.0',
            'description': 'Test component',
            'exposed_apis': [],
            'labels': {}
        }
        
        # Component doesn't exist
        mock_get.return_value.status_code = 404
        # Component creation succeeds  
        mock_post.return_value.status_code = 200
        
        result = self.client.sync_component(component_data)
        
        self.assertTrue(result)
        mock_get.assert_called_once()
        mock_post.assert_called_once()
    
    @patch('requests.Session.get')
    @patch('requests.Session.put')
    def test_sync_component_update(self, mock_put, mock_get):
        """Test updating an existing component."""
        component_data = {
            'component_registry_ref': 'test-registry',
            'component_name': 'existing-component',
            'component_version': '2.0.0',
            'description': 'Updated component',
            'exposed_apis': [],
            'labels': {}
        }
        
        # Component exists
        mock_get.return_value.status_code = 200
        # Component update succeeds
        mock_put.return_value.status_code = 200
        
        result = self.client.sync_component(component_data)
        
        self.assertTrue(result)
        mock_get.assert_called_once()
        mock_put.assert_called_once()


class TestKubernetesComponentReader(unittest.TestCase):
    """Test the KubernetesComponentReader class."""
    
    @patch('kubernetes.config.load_kube_config')
    @patch('kubernetes.client.CustomObjectsApi')
    def test_get_components(self, mock_api_class, mock_config):
        """Test reading components from Kubernetes."""
        mock_api = Mock()
        mock_api_class.return_value = mock_api
        
        # Mock API response
        mock_response = {
            'items': [
                {'metadata': {'name': 'component1'}},
                {'metadata': {'name': 'component2'}}
            ]
        }
        mock_api.list_namespaced_custom_object.return_value = mock_response
        
        reader = KubernetesComponentReader()
        components = reader.get_components(['test-namespace'])
        
        self.assertEqual(len(components), 2)
        self.assertEqual(components[0]['metadata']['name'], 'component1')
        
        mock_api.list_namespaced_custom_object.assert_called_with(
            group="oda.tmforum.org",
            version="v1beta3",
            namespace="test-namespace",
            plural="components"
        )


class TestComponentSyncTool(unittest.TestCase):
    """Test the ComponentSyncTool integration."""
    
    def setUp(self):
        registry_config = RegistryConfig(url="http://test-registry")
        self.sync_config = SyncConfig(
            registry=registry_config,
            namespaces=['test-namespace'],
            registry_name='test-registry',
            dry_run=True
        )
    
    @patch('k8s_component_sync.KubernetesComponentReader')
    @patch('k8s_component_sync.RegistryClient')
    def test_sync_dry_run(self, mock_registry_client, mock_k8s_reader):
        """Test dry run synchronization."""
        # Mock Kubernetes components
        mock_reader_instance = Mock()
        mock_k8s_reader.return_value = mock_reader_instance
        mock_reader_instance.get_components.return_value = [
            {
                'metadata': {'name': 'test-component'},
                'spec': {'version': '1.0.0', 'description': 'Test'}
            }
        ]
        
        # Mock registry client
        mock_client_instance = Mock()
        mock_registry_client.return_value = mock_client_instance
        
        sync_tool = ComponentSyncTool(self.sync_config)
        result = sync_tool.sync()
        
        self.assertTrue(result)
        mock_reader_instance.get_components.assert_called_once_with(['test-namespace'])
        # In dry run, registry methods should not be called
        mock_client_instance.create_registry.assert_not_called()
        mock_client_instance.sync_component.assert_not_called()


class TestIntegrationScenarios(unittest.TestCase):
    """Test realistic integration scenarios."""
    
    def test_full_component_transformation(self):
        """Test transformation of a complete ODA component."""
        # Load the sample component from the attachment
        with open('TEST/component.json', 'r') as f:
            k8s_component = json.load(f)
        
        transformer = ComponentTransformer()
        result = transformer.transform_component(k8s_component, "cluster-registry")
        
        # Verify transformation results
        self.assertEqual(result['component_name'], "demo-a-productcatalogmanagement")
        self.assertEqual(result['component_version'], "0.0.1")
        self.assertIn("Product Catalog", result['description'])
        
        # Should have APIs from core, management, and security functions
        self.assertGreater(len(result['exposed_apis']), 0)
        
        # Check that labels include ODA-specific metadata
        self.assertIn('functionalBlock', result['labels'])
        self.assertEqual(result['labels']['functionalBlock'], 'CoreCommerce')
    
    def test_api_url_construction(self):
        """Test proper API URL construction from K8s component data."""
        transformer = ComponentTransformer()
        
        api_data = {
            'name': 'test-api',
            'path': '/api/v1/test',
            'port': 8080,
            'implementation': 'test-service',
            'specification': ['https://example.com/swagger.json']
        }
        
        result = transformer._transform_exposed_api(api_data, 'test-component')
        
        self.assertEqual(result['url'], 'http://test-service:8080/api/v1/test')
        self.assertEqual(result['oas_specification'], 'https://example.com/swagger.json')
        self.assertEqual(result['name'], 'test-component-test-api')


if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2)