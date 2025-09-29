# Component Registry Service

A FastAPI-based REST service for managing ODA Component Registries, Components, and their Exposed APIs following the TM Forum ODA Canvas specification.

## Features

- **CRUD Operations** for Component Registries, Components, and Exposed APIs
- **RESTful API** with OpenAPI/Swagger documentation
- **SQLite Database** for data persistence
- **Input Validation** using Pydantic models
- **Comprehensive Testing** with pytest
- **Docker Support** for containerized deployment
- **Health Check** endpoint for monitoring

## Data Model

The service implements the following data model from the Component Registry specification:

### ComponentRegistry

* name (unique name)
* url (endpoint for accessing the component registry)
* type (upstream/downstream/self)
* labels (list of key-value pairs)

### ExposedAPI

* name (name of exposed api)
* oasSpecification (url to openAPI specification of this exposed api)
* url (endoint for accessing the exposed API)
* labels (list of key-value pairs)

### Component

* componentRegistryRef (reference to ComponentRegistry)
* componentName (unique together with ComponentRegistry)
* exposedAPIs (list of ExposedAPI)
* labels (list of key-value pairs)

## Quick Start

### Prerequisites
- Python 3.11 or higher
- pip

### Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the service:
```bash
python run.py
```

The service will be available at `http://localhost:8000`

### API Documentation

Once running, you can access:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`
- **Health Check**: `http://localhost:8000/health`

## Docker Deployment

### Build and run with Docker:
```bash
docker build -t component-registry-service .
docker run -p 8000:8000 component-registry-service
```

### Or use Docker Compose:
```bash
docker-compose up
```

## API Endpoints

### Component Registries
- `POST /registries` - Create a new Component Registry
- `GET /registries` - Get all Component Registries (supports pagination)
- `GET /registries/{name}` - Get a specific Component Registry
- `PUT /registries/{name}` - Update a Component Registry
- `DELETE /registries/{name}` - Delete a Component Registry
- `GET /registries/{name}/components` - Get all Components for a registry

### Components
- `POST /components` - Create a new Component
- `GET /components` - Get all Components (supports filtering and pagination)
- `GET /components/{registry_ref}/{component_name}` - Get a specific Component
- `PUT /components/{registry_ref}/{component_name}` - Update a Component
- `DELETE /components/{registry_ref}/{component_name}` - Delete a Component

### Utility
- `GET /health` - Health check endpoint
- `GET /` - Service information

## Example Usage

### Create a Component Registry
```bash
curl -X POST "http://localhost:8000/registries" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "production-registry",
    "url": "https://registry.example.com/api",
    "type": "upstream",
    "labels": {
      "environment": "production",
      "region": "us-east-1"
    }
  }'
```

### Create a Component
```bash
curl -X POST "http://localhost:8000/components" \
  -H "Content-Type: application/json" \
  -d '{
    "component_registry_ref": "production-registry",
    "component_name": "product-catalog-service",
    "exposed_apis": [
      {
        "name": "product-catalog-api",
        "oas_specification": "https://api.example.com/swagger.json",
        "url": "https://api.example.com/v1/products",
        "labels": {
          "version": "v1"
        }
      }
    ],
    "labels": {
      "team": "catalog-team",
      "environment": "production"
    }
  }'
```

## Testing

Run the test suite:
```bash
pytest test_main.py -v
```

The tests cover:
- All CRUD operations
- Error handling
- Input validation
- Query parameters and filtering
- Health check endpoints

## Development

### Project Structure
```
component-registry-service/
├── __init__.py          # Package initialization
├── main.py              # FastAPI application
├── models.py            # Pydantic data models
├── database.py          # SQLAlchemy database models
├── crud.py              # Database CRUD operations
├── run.py               # Startup script
├── test_main.py         # Test suite
├── requirements.txt     # Python dependencies
├── Dockerfile           # Docker configuration
├── docker-compose.yml   # Docker Compose configuration
└── README.md            # This file
```

### Configuration

The service uses SQLite by default for simplicity. For production use, you may want to configure a different database by modifying the `SQLALCHEMY_DATABASE_URL` in `database.py`.

## Security Considerations

This is a basic implementation for demonstration purposes. For production deployment, consider:
- Authentication and authorization
- Input sanitization and rate limiting
- HTTPS/TLS configuration
- Database security and connection pooling
- Logging and monitoring
- CORS configuration for specific origins

## Contributing

This service follows the TM Forum ODA Canvas development guidelines:
1. Use BDD for new features
2. Include comprehensive tests
3. Follow the Kubernetes Operator Pattern where applicable
4. Document design decisions