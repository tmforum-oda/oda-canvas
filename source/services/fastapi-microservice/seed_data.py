"""
Sample data seeder for the ODA Canvas microservice.
Creates initial test data for Labels, Registries, Components, and Exposed APIs.
"""

from sqlalchemy.orm import Session
from database import SessionLocal, init_db
import crud
import schemas

def seed_data():
    """Seed the database with ODA Canvas sample data"""
    db = SessionLocal()
    
    try:
        # Create sample ODA Canvas data
        
        # Create sample labels
        labels_data = [
            {"key": "team", "value": "odafans"},
            {"key": "environment", "value": "production"},
            {"key": "environment", "value": "development"},
            {"key": "version", "value": "v1.0"},
            {"key": "protocol", "value": "REST"},
            {"key": "protocol", "value": "GraphQL"},
            {"key": "domain", "value": "productcatalog"},
            {"key": "domain", "value": "customer"},
            {"key": "security", "value": "oauth2"},
            {"key": "region", "value": "europe"}
        ]
        
        created_labels = []
        for label_data in labels_data:
            existing_label = crud.label_crud.get_by_key_value(db, label_data["key"], label_data["value"])
            if not existing_label:
                label = crud.label_crud.create(db, schemas.LabelCreate(**label_data))
                created_labels.append(label)
                print(f"Created label: {label.key}={label.value}")
            else:
                created_labels.append(existing_label)
                print(f"Label already exists: {existing_label.key}={existing_label.value}")
        
        # Create sample registries
        registries_data = [
            {
                "name": "local-registry",
                "type": schemas.RegistryTypeEnum.self,
                "url": "http://localhost:8080/registry",
                "label_ids": [created_labels[0].id, created_labels[1].id]  # team:odafans, environment:production
            },
            {
                "name": "upstream-registry",
                "type": schemas.RegistryTypeEnum.upstream,
                "url": "https://upstream.example.com/registry",
                "label_ids": [created_labels[9].id]  # region:europe
            },
            {
                "name": "development-registry",
                "type": schemas.RegistryTypeEnum.downstream,
                "url": "http://dev.example.com/registry",
                "label_ids": [created_labels[2].id]  # environment:development
            }
        ]
        
        created_registries = []
        for registry_data in registries_data:
            existing_registry = crud.registry_crud.get_by_name(db, registry_data["name"])
            if not existing_registry:
                registry = crud.registry_crud.create(db, schemas.RegistryCreate(**registry_data))
                created_registries.append(registry)
                print(f"Created registry: {registry.name}")
            else:
                created_registries.append(existing_registry)
                print(f"Registry already exists: {existing_registry.name}")
        
        # Create sample components
        if created_registries:
            components_data = [
                {
                    "registry_name": created_registries[0].name,  # local-registry
                    "name": "prodcat",
                    "label_ids": [created_labels[0].id, created_labels[6].id]  # team:odafans, domain:productcatalog
                },
                {
                    "registry_name": created_registries[0].name,  # local-registry
                    "name": "customer-mgmt",
                    "label_ids": [created_labels[7].id]  # domain:customer
                },
                {
                    "registry_name": created_registries[1].name,  # upstream-registry
                    "name": "external-api-gateway",
                    "label_ids": [created_labels[8].id]  # security:oauth2
                }
            ]
            
            created_components = []
            for component_data in components_data:
                existing_component = crud.component_crud.get_by_registry_and_name(
                    db, component_data["registry_name"], component_data["name"]
                )
                if not existing_component:
                    component = crud.component_crud.create(db, schemas.ComponentCreate(**component_data))
                    created_components.append(component)
                    print(f"Created component: {component.name} in {component.registry_name}")
                else:
                    created_components.append(existing_component)
                    print(f"Component already exists: {existing_component.name}")
            
            # Create sample exposed APIs
            if created_components:
                exposed_apis_data = [
                    {
                        "registry_name": created_registries[0].name,
                        "component_name": created_components[0].name,  # prodcat
                        "name": "pcapi",
                        "url": "http://localhost:8080/prodcat/api/v1",
                        "oas_specification": '{"openapi": "3.0.0", "info": {"title": "Product Catalog API", "version": "1.0.0"}}',
                        "status": schemas.APIStatusEnum.ready,
                        "label_ids": [created_labels[3].id, created_labels[4].id]  # version:v1.0, protocol:REST
                    },
                    {
                        "registry_name": created_registries[0].name,
                        "component_name": created_components[1].name,  # customer-mgmt
                        "name": "customer-api",
                        "url": "http://localhost:8080/customer/api/v1",
                        "oas_specification": None,
                        "status": schemas.APIStatusEnum.pending,
                        "label_ids": [created_labels[5].id]  # protocol:GraphQL
                    },
                    {
                        "registry_name": created_registries[1].name,
                        "component_name": created_components[2].name,  # external-api-gateway
                        "name": "gateway-api",
                        "url": "https://api.example.com/gateway/v1",
                        "oas_specification": '{"openapi": "3.0.0", "info": {"title": "API Gateway", "version": "1.0.0"}}',
                        "status": schemas.APIStatusEnum.ready,
                        "label_ids": [created_labels[8].id]  # security:oauth2
                    }
                ]
                
                for api_data in exposed_apis_data:
                    try:
                        api = crud.exposed_api_crud.create(db, schemas.ExposedAPICreate(**api_data))
                        print(f"Created exposed API: {api.name} for component {api.component_name}")
                    except Exception as e:
                        print(f"API might already exist or error occurred: {e}")
        
        print("ODA Canvas sample data seeding completed successfully!")
        
    except Exception as e:
        print(f"Error seeding data: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    # Initialize database first
    init_db()
    # Then seed with sample data
    seed_data()