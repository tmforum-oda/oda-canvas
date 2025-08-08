# TMF639 Resource Inventory Management API

This is a TMF639 Resource Inventory Management API implementation for the ODA Canvas that provides read-only access to ODA Canvas resources including Components and ExposedAPIs.

## Overview

The TMF639 Resource Inventory service wraps the Kubernetes API to provide TMF-compliant access to ODA Canvas resources. It offers read-only operations to query Components and ExposedAPIs deployed in the ODA Canvas Kubernetes cluster.

## Features

- **Read-only Access**: Only supports list and retrieve operations for security
- **Component Resources**: Access to ODA Components with their metadata and status
- **ExposedAPI Resources**: Access to exposed APIs with their configuration details
- **TMF639 Compliance**: Full compliance with TMF639 Resource Inventory Management specification
- **Kubernetes Integration**: Direct integration with ODA Canvas Kubernetes custom resources

## API Endpoints

### Resources
- `GET /tmf-api/resourceInventoryManagement/v5/resource` - List all resources (Components and ExposedAPIs)
- `GET /tmf-api/resourceInventoryManagement/v5/resource/{id}` - Retrieve a specific resource

### Hub Management
- `POST /tmf-api/resourceInventoryManagement/v5/hub` - Register for notifications
- `DELETE /tmf-api/resourceInventoryManagement/v5/hub/{id}` - Unregister from notifications

### Notification Listeners
- `POST /listener/resourceCreateEvent` - Resource creation notifications
- `POST /listener/resourceStateChangeEvent` - Resource state change notifications
- `POST /listener/resourceDeleteEvent` - Resource deletion notifications

## Resource Mapping

### ODA Components → TMF639 Resources
- Component metadata mapped to resource characteristics
- Component status mapped to resource operational state
- Component namespace mapped to resource place

### ExposedAPIs → TMF639 Resources  
- API specification mapped to resource characteristics
- API status mapped to resource operational state
- API configuration mapped to resource properties

## Configuration

### Environment Variables
- `KUBERNETES_NAMESPACE`: Target namespace (default: 'canvas')
- `KUBERNETES_SERVICE_HOST`: Automatically set in cluster
- `SERVER_URL`: Override server URL
- `NODE_ENV`: Environment mode

### Database Configuration
- MongoDB connection for event subscriptions and notifications
- Database name: `resinv`
- Default host: `canvas-resinv-mongodb`

## Running the Service

### Development
```bash
npm install
npm start
```

### Docker
```bash
docker build -t tmf639-resource-inventory .
docker run -p 8639:8639 tmf639-resource-inventory
```

### Kubernetes Deployment
The service requires appropriate RBAC permissions to access ODA Canvas custom resources:
- Components (components.oda.tmforum.org)
- ExposedAPIs (exposedapis.oda.tmforum.org)

## API Documentation

Once running, the API documentation is available at:
- Swagger UI: `http://localhost:8639/tmf-api/resourceInventoryManagement/v5/api-docs`
- OpenAPI Spec: `http://localhost:8639/tmf-api/resourceInventoryManagement/v5/openapi`

## Security

- Read-only access ensures no modifications to ODA Canvas resources
- Kubernetes RBAC controls access to underlying resources
- TMF639 standard compliance for industry interoperability

## Dependencies

- Node.js >= 14
- Kubernetes cluster with ODA Canvas installed
- MongoDB for event management
- Appropriate Kubernetes RBAC permissions

## License

Licensed under the same terms as the ODA Canvas project.
