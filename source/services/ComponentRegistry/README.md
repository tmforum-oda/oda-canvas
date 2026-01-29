# TMF639 Resource Inventory Management Service

A FastAPI-based REST service for managing Resources following the TM Forum OpenAPI TMF-639 specification **v5.0.0**.

## Features

- **CRUD Operations**: Full support for Create, Read, Update, and Delete operations on Resources
- **TMF639 v5.0.0 Compliance**: Implements the TM Forum TMF-639 Resource Inventory Management API v5.0.0
- **SQLAlchemy ORM**: Uses SQLAlchemy for database persistence (SQLite by default, configurable for PostgreSQL/MySQL)
- **FastAPI Framework**: Modern, fast web framework with automatic API documentation
- **Event Subscriptions**: Support for registering event listeners (hub endpoints with GET support)
- **Advanced Filtering**: Support for pagination, sorting, and filtering

## What's New in v5.0.0

- **New API Path**: `/resourceInventory/v5` (instead of `/tmf-api/resourceInventoryManagement/v4`)
- **New Resource Fields**:
  - `validFor`: Time period for resource validity
  - `resourceOrderItem`: Related resource order items
  - `supportingResource`: List of supporting resources
  - `activationFeature`: Configuration features
  - `intent`: Intent reference
  - `externalIdentifier`: External system identifiers
  - `place`: Now an array instead of single object
- **New Resource Status Values**: `installed`, `not exists`, `pendingRemoval`, `planned`
- **Enhanced Hub/Event Subscription**: Added GET endpoint to retrieve subscriptions
- **Advanced Query Parameters**: `before`, `after`, `sort`, `filter` for resource listing
- **Improved Related Party Structure**: Using `RelatedPartyRefOrPartyRoleRef`

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
│   ├── TMF639-Resource_Inventory_Management-v5.0.0.oas.yaml
│   └── TMF639_Resource_Inventory_Management_API_v4.0.0_swagger.json
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
   docker build -t tmf639-resource-inventory:v5.0.0 .
   ```

2. **Run the container:**
   ```bash
   docker run -p 8080:8080 tmf639-resource-inventory:v5.0.0
   ```

## API Documentation

Once the service is running, you can access:

- **Swagger UI**: http://localhost:8080/docs
- **ReDoc**: http://localhost:8080/redoc
- **OpenAPI JSON**: http://localhost:8080/openapi.json

## API Endpoints

### Resource Management (v5.0.0)

- `GET /resourceInventory/v5/resource` - List all resources (with filtering, sorting, pagination)
- `POST /resourceInventory/v5/resource` - Create a new resource
- `GET /resourceInventory/v5/resource/{id}` - Retrieve a specific resource
- `PATCH /resourceInventory/v5/resource/{id}` - Update a resource
- `DELETE /resourceInventory/v5/resource/{id}` - Delete a resource

### Event Subscriptions (v5.0.0)

- `POST /resourceInventory/v5/hub` - Create a subscription (hub)
- `GET /resourceInventory/v5/hub/{id}` - Retrieve a subscription (hub) ⭐ **NEW in v5.0.0**
- `DELETE /resourceInventory/v5/hub/{id}` - Delete a subscription (hub)

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

## Example Usage (v5.0.0)

### Create a Resource with ID

```bash
curl -X POST "http://localhost:8080/resourceInventory/v5/resource" \
  -H "Content-Type: application/json" \
  -d '{
    "id": "resource-12345",
    "name": "Server-001",
    "category": "Physical",
    "description": "Production web server",
    "resourceStatus": "available",
    "administrativeState": "unlocked",
    "operationalState": "enable",
    "usageState": "idle",
    "validFor": {
      "startDateTime": "2025-01-01T00:00:00Z",
      "endDateTime": "2025-12-31T23:59:59Z"
    },
    "place": [
      {
        "id": "datacenter-01",
        "name": "Main Data Center",
        "role": "installation"
      }
    ],
    "externalIdentifier": [
      {
        "id": "EXT-12345",
        "owner": "Legacy System",
        "externalIdentifierType": "AssetID"
      }
    ]
  }'
```

### Create a Resource without ID (Auto-generated)

```bash
curl -X POST "http://localhost:8080/resourceInventory/v5/resource" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Server-002",
    "category": "Physical",
    "resourceStatus": "planned"
  }'
```

### List Resources with Filtering

```bash
curl -X GET "http://localhost:8080/resourceInventory/v5/resource?limit=10&offset=0&sort=name"
```

### Get a Specific Resource

```bash
curl -X GET "http://localhost:8080/resourceInventory/v5/resource/resource-12345"
```

### Update a Resource

```bash
curl -X PATCH "http://localhost:8080/resourceInventory/v5/resource/resource-12345" \
  -H "Content-Type: application/json" \
  -d '{
    "description": "Updated production web server",
    "resourceStatus": "reserved",
    "activationFeature": [
      {
        "id": "feature-001",
        "name": "Auto-scaling",
        "isEnabled": true
      }
    ]
  }'
```

### Delete a Resource

```bash
curl -X DELETE "http://localhost:8080/resourceInventory/v5/resource/resource-12345"
```

### Create Event Subscription (Hub)

```bash
curl -X POST "http://localhost:8080/resourceInventory/v5/hub" \
  -H "Content-Type: application/json" \
  -d '{
    "callback": "https://myserver.com/listener",
    "query": "eventType=ResourceCreateEvent"
  }'
```

### Get Event Subscription (Hub) ⭐ NEW

```bash
curl -X GET "http://localhost:8080/resourceInventory/v5/hub/{hub-id}"
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

## TMF639 v5.0.0 Compliance

This implementation follows the TM Forum TMF-639 Resource Inventory Management API specification v5.0.0. It includes:

- Resource entity with full attribute support including v5.0.0 new fields
- Characteristics, relationships, and attachments
- Related parties using new `RelatedPartyRefOrPartyRoleRef` structure
- Places as array (changed from v4.0.0)
- Administrative, operational, resource (extended), and usage state enumerations
- Event subscription mechanisms with GET support
- External identifiers for cross-system integration
- Supporting resources and activation features
- Intent reference support
- Proper HTTP status codes and error responses
- Advanced query parameters (filter, sort, before, after)

## Migration from v4.0.0 to v5.0.0

If you are migrating from v4.0.0:

1. **Update API paths**: Change `/tmf-api/resourceInventoryManagement/v4` to `/resourceInventory/v5`
2. **Update place structure**: `place` is now an array instead of a single object
3. **Add new optional fields**: `validFor`, `resourceOrderItem`, `supportingResource`, `activationFeature`, `intent`, `externalIdentifier`
4. **Update status values**: New values available for `resourceStatus`
5. **Hub GET support**: You can now retrieve hub subscriptions by ID

## License

This project is part of the ODA Canvas Reference Implementation.

## Contributing

Please refer to the main ODA Canvas contribution guidelines in the repository root.

# Buildautomation and Versioning

The build and release process for docker images is described here:
[docs/developer/work-with-dockerimages.md](../../../../docs/developer/work-with-dockerimages.md)

