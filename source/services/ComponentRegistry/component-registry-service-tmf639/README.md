# TMF639 Resource Inventory Management Service

A FastAPI-based REST service for managing Resources following the TM Forum OpenAPI TMF-639 specification.

## Features

- **CRUD Operations**: Full support for Create, Read, Update, and Delete operations on Resources
- **TMF639 Compliance**: Implements the TM Forum TMF-639 Resource Inventory Management API v4.0.0
- **SQLAlchemy ORM**: Uses SQLAlchemy for database persistence (SQLite by default, configurable for PostgreSQL/MySQL)
- **FastAPI Framework**: Modern, fast web framework with automatic API documentation
- **Event Subscriptions**: Support for registering event listeners (hub endpoints)

## Project Structure

```
component-registry-service-tmf639/
├── app/
│   ├── __init__.py          # Package initialization
│   ├── main.py              # FastAPI application and endpoints
│   ├── database.py          # Database configuration
│   ├── models.py            # SQLAlchemy database models
│   ├── schemas.py           # Pydantic schemas for validation
│   └── crud.py              # CRUD operations
├── openapi/                 # OpenAPI specification
├── Dockerfile               # Container image definition
├── requirements.txt         # Python dependencies
├── .gitignore              # Git ignore file
└── README.md               # This file
```

## Installation

### Prerequisites

- Python 3.11 or higher
- pip (Python package manager)

### Local Setup

1. **Create a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the service:**
   ```bash
   python -m app.main
   ```
   
   Or using uvicorn directly:
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8080
   ```

The service will start on `http://localhost:8080`

### Docker Setup

1. **Build the Docker image:**
   ```bash
   docker build -t tmf639-resource-inventory:latest .
   ```

2. **Run the container:**
   ```bash
   docker run -p 8080:8080 tmf639-resource-inventory:latest
   ```

## API Documentation

Once the service is running, you can access:

- **Swagger UI**: http://localhost:8080/docs
- **ReDoc**: http://localhost:8080/redoc
- **OpenAPI JSON**: http://localhost:8080/openapi.json

## API Endpoints

### Resource Management

- `GET /tmf-api/resourceInventoryManagement/v4/resource` - List all resources
- `POST /tmf-api/resourceInventoryManagement/v4/resource` - Create a new resource
- `GET /tmf-api/resourceInventoryManagement/v4/resource/{id}` - Retrieve a specific resource
- `PATCH /tmf-api/resourceInventoryManagement/v4/resource/{id}` - Update a resource
- `DELETE /tmf-api/resourceInventoryManagement/v4/resource/{id}` - Delete a resource

### Event Subscriptions

- `POST /tmf-api/resourceInventoryManagement/v4/hub` - Register an event listener
- `DELETE /tmf-api/resourceInventoryManagement/v4/hub/{id}` - Unregister an event listener

### Health Check

- `GET /health` - Service health check

## Configuration

The service can be configured using environment variables:

- `DATABASE_URL`: Database connection string (default: `sqlite:///./resource_inventory.db`)
- `HOST`: Host address to bind (default: `0.0.0.0`)
- `PORT`: Port to listen on (default: `8080`)

### Database Configuration

**SQLite (default):**
```bash
export DATABASE_URL="sqlite:///./resource_inventory.db"
```

**PostgreSQL:**
```bash
export DATABASE_URL="postgresql://user:password@localhost/dbname"
```

**MySQL:**
```bash
export DATABASE_URL="mysql+pymysql://user:password@localhost/dbname"
```

## Example Usage

### Create a Resource

```bash
curl -X POST "http://localhost:8080/tmf-api/resourceInventoryManagement/v4/resource" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Server-001",
    "category": "Physical",
    "description": "Production web server",
    "resourceStatus": "available",
    "administrativeState": "unlocked",
    "operationalState": "enable",
    "usageState": "idle"
  }'
```

### List Resources

```bash
curl -X GET "http://localhost:8080/tmf-api/resourceInventoryManagement/v4/resource?limit=10&offset=0"
```

### Get a Specific Resource

```bash
curl -X GET "http://localhost:8080/tmf-api/resourceInventoryManagement/v4/resource/{id}"
```

### Update a Resource

```bash
curl -X PATCH "http://localhost:8080/tmf-api/resourceInventoryManagement/v4/resource/{id}" \
  -H "Content-Type: application/json" \
  -d '{
    "description": "Updated description",
    "resourceStatus": "reserved"
  }'
```

### Delete a Resource

```bash
curl -X DELETE "http://localhost:8080/tmf-api/resourceInventoryManagement/v4/resource/{id}"
```

## Development

### Running Tests

```bash
pytest
```

### Code Formatting

```bash
black app/
```

### Type Checking

```bash
mypy app/
```

## TMF639 Compliance

This implementation follows the TM Forum TMF-639 Resource Inventory Management API specification v4.0.0. It includes:

- Resource entity with full attribute support
- Characteristics, relationships, and attachments
- Related parties and notes
- Administrative, operational, resource, and usage state enumerations
- Event subscription mechanisms
- Proper HTTP status codes and error responses

## License

This project is part of the ODA Canvas Reference Implementation.

## Contributing

Please refer to the main ODA Canvas contribution guidelines in the repository root.