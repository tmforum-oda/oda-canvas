# TMF628 Performance Management API - Carbon Intensity Service

A Node.js implementation of the TMF628 Performance Management API, specialized for serving carbon intensity measurements to support carbon-aware workload scheduling and scaling in ODA Canvas.

## Overview

This service provides carbon intensity data through a TMF Forum Open API-compliant interface. It serves real-time carbon intensity measurements (in gCO2eq/kWh) for different geographic regions, enabling ODA Components to make carbon-aware decisions for workload placement, scaling, and scheduling.

The implementation follows the TMF628 Performance Management API standard v5.0.0 with extensions to support dynamic data updates and administrative operations.

## Features

- **TMF628 Standard Compliance**: Implements the TMF Forum Open API v5.0.0 specification
- **Real-time Data Updates**: Hot-reload capability with file watching (configurable)
- **Dynamic Updates**: In-memory updates via PATCH operations without service restart
- **Flexible Querying**: Filter by timestamp, region, with pagination and field selection
- **Smart Time Matching**: Exact timestamp matching with automatic time-of-day fallback
- **Administrative Operations**: Reload data from file and retrieve statistics

## Architecture

```
┌─────────────────────────────────────────────────┐
│  Express Server (Port 8628)                     │
│  + OpenAPI Validator                            │
│  + Swagger UI (/api-docs)                       │
└─────────────────┬───────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────┐
│  PerformanceMeasurementController               │
│  - Route handling                               │
│  - Parameter extraction                         │
└─────────────────┬───────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────┐
│  PerformanceMeasurementService                  │
│  - Business logic                               │
│  - Filtering & pagination                       │
│  - Data updates                                 │
└─────────────────┬───────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────┐
│  DataLoader                                     │
│  - File reading                                 │
│  - Hot-reload/watch                             │
│  - In-memory storage                            │
└─────────────────┬───────────────────────────────┘
                  │
         carbon-intensity-data.json
```

## API Endpoints

### Base Path
```
http://localhost:8628/tmf-api/performance/v5
```

### Standard TMF628 Operations

#### 1. List Performance Measurements

Retrieve a collection of carbon intensity measurements with optional filtering.

**Endpoint:** `GET /performanceMeasurement`

**Query Parameters:**

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `validForTimestamp` | ISO 8601 DateTime | Filter measurements by timestamp. Returns measurements where the timestamp falls within the `validFor` period. Supports smart fallback to time-of-day matching if exact date not found. | `2026-05-30T10:30:00Z` |
| `region` | String | Filter by region tag | `us-central1-c` |
| `fields` | String | Comma-separated list of fields to include in response | `id,validFor,tag` |
| `offset` | Integer | Starting index for pagination | `0` |
| `limit` | Integer | Maximum number of results to return | `10` |

**Example Requests:**

```bash
# Get all measurements
curl http://localhost:8628/tmf-api/performance/v5/performanceMeasurement

# Filter by timestamp
curl "http://localhost:8628/tmf-api/performance/v5/performanceMeasurement?validForTimestamp=2026-05-30T10:30:00Z"

# Filter by region
curl "http://localhost:8628/tmf-api/performance/v5/performanceMeasurement?region=us-central1-c"

# Combined filters with pagination
curl "http://localhost:8628/tmf-api/performance/v5/performanceMeasurement?region=us-central1-c&validForTimestamp=2026-05-30T10:30:00Z&limit=5"

# Select specific fields
curl "http://localhost:8628/tmf-api/performance/v5/performanceMeasurement?fields=id,performanceIndicatorValue,tag"
```

**Response Example:**

```json
[
  {
    "id": "ci-us-central1-c-001",
    "href": "/tmf-api/performance/v5/performanceMeasurement/ci-us-central1-c-001",
    "description": "Carbon intensity measurement for us-central1-c region",
    "@type": "PerformanceMeasurementAtomic",
    "@baseType": "PerformanceMeasurement",
    "validFor": {
      "startDateTime": "2026-05-30T00:00:00Z",
      "endDateTime": "2026-05-30T00:30:00Z"
    },
    "performanceIndicatorValue": [
      {
        "performanceIndicatorSpecification": {
          "id": "pi-carbon-intensity",
          "name": "Carbon Intensity",
          "indicatorCategory": "Environmental",
          "indicatorUnit": "gCO2eq/kWh",
          "@type": "PerformanceIndicatorSpecification"
        },
        "observedValue": "500"
      }
    ],
    "tag": {
      "region": "us-central1-c",
      "country": "United States",
      "gridOperator": "MISO"
    }
  }
]
```

**Time Filtering Behavior:**

The `validForTimestamp` parameter implements intelligent time matching:

1. **Exact Match**: First attempts to find measurements where the timestamp falls within the `validFor` period
2. **Time-of-Day Fallback**: If no exact match is found, matches by time-of-day only (ignoring the date)
3. **Date Adjustment**: When using time-of-day matching, automatically adjusts the returned dates to match the requested date

This enables querying for "what is the carbon intensity at 10:30 AM today" even if the data file only contains historical dates.

#### 2. Retrieve Performance Measurement by ID

Retrieve a specific carbon intensity measurement by its ID.

**Endpoint:** `GET /performanceMeasurement/{id}`

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `id` | String | Unique identifier of the PerformanceMeasurement |

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `fields` | String | Comma-separated list of fields to include in response |

**Example Requests:**

```bash
# Get measurement by ID
curl http://localhost:8628/tmf-api/performance/v5/performanceMeasurement/ci-us-central1-c-001

# Get specific fields only
curl "http://localhost:8628/tmf-api/performance/v5/performanceMeasurement/ci-us-central1-c-001?fields=id,performanceIndicatorValue"
```

**Response Example:**

```json
{
  "id": "ci-us-central1-c-001",
  "href": "/tmf-api/performance/v5/performanceMeasurement/ci-us-central1-c-001",
  "description": "Carbon intensity measurement for us-central1-c region",
  "@type": "PerformanceMeasurementAtomic",
  "@baseType": "PerformanceMeasurement",
  "validFor": {
    "startDateTime": "2026-05-30T00:00:00Z",
    "endDateTime": "2026-05-30T00:30:00Z"
  },
  "performanceIndicatorValue": [
    {
      "performanceIndicatorSpecification": {
        "id": "pi-carbon-intensity",
        "name": "Carbon Intensity",
        "indicatorCategory": "Environmental",
        "indicatorUnit": "gCO2eq/kWh",
        "@type": "PerformanceIndicatorSpecification"
      },
      "observedValue": "500"
    }
  ],
  "tag": {
    "region": "us-central1-c",
    "country": "United States",
    "gridOperator": "MISO"
  }
}
```

**Error Response (404):**

```json
{
  "message": "PerformanceMeasurement with id ci-invalid-id not found"
}
```

### Extended Operations (Non-Standard TMF628)

#### 3. Update Performance Measurement

Dynamically update specific fields of a carbon intensity measurement in-memory without restarting the service.

**Endpoint:** `PATCH /performanceMeasurement/{id}`

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `id` | String | Unique identifier of the PerformanceMeasurement to update |

**Request Body:**

Partial `PerformanceMeasurement` object containing only the fields to update. The `id` and `href` fields cannot be changed.

**Example Request:**

```bash
curl -X PATCH http://localhost:8628/tmf-api/performance/v5/performanceMeasurement/ci-us-central1-c-001 \
  -H "Content-Type: application/json" \
  -d '{
    "performanceIndicatorValue": [
      {
        "performanceIndicatorSpecification": {
          "id": "pi-carbon-intensity",
          "name": "Carbon Intensity",
          "indicatorCategory": "Environmental",
          "indicatorUnit": "gCO2eq/kWh",
          "@type": "PerformanceIndicatorSpecification"
        },
        "observedValue": "350"
      }
    ]
  }'
```

**Example: Update Carbon Intensity Value**

```bash
# Update just the carbon intensity value
curl -X PATCH http://localhost:8628/tmf-api/performance/v5/performanceMeasurement/ci-us-central1-c-001 \
  -H "Content-Type: application/json" \
  -d '{
    "performanceIndicatorValue": [
      {
        "performanceIndicatorSpecification": {
          "id": "pi-carbon-intensity",
          "name": "Carbon Intensity",
          "indicatorCategory": "Environmental",
          "indicatorUnit": "gCO2eq/kWh",
          "@type": "PerformanceIndicatorSpecification"
        },
        "observedValue": "250"
      }
    ],
    "description": "Updated carbon intensity - cleaner energy mix"
  }'
```

**Response:**

Returns the updated `PerformanceMeasurement` object with all fields (both updated and unchanged).

**Note:** Updates are in-memory only. They will be lost if:
- The service restarts
- The data file is reloaded (manual or via file watching)
- The admin reload endpoint is called

## Data Structure

### PerformanceMeasurement Schema

Carbon intensity measurements follow the TMF628 `PerformanceMeasurementAtomic` structure:

```json
{
  "id": "string",                         // Unique identifier
  "href": "string",                       // Self-reference URL
  "description": "string",                // Human-readable description
  "@type": "PerformanceMeasurementAtomic",
  "@baseType": "PerformanceMeasurement",
  "validFor": {
    "startDateTime": "ISO 8601",         // Start of measurement period
    "endDateTime": "ISO 8601"            // End of measurement period
  },
  "performanceIndicatorValue": [
    {
      "performanceIndicatorSpecification": {
        "id": "pi-carbon-intensity",
        "name": "Carbon Intensity",
        "indicatorCategory": "Environmental",
        "indicatorUnit": "gCO2eq/kWh",
        "@type": "PerformanceIndicatorSpecification"
      },
      "observedValue": "string"          // Carbon intensity value
    }
  ],
  "tag": {
    "region": "string",                   // Geographic region identifier
    "country": "string",                  // Country name
    "gridOperator": "string"              // Electricity grid operator
  }
}
```

## Installation and Usage

### Prerequisites

- Node.js 14+ and npm

### Local Development

1. **Install dependencies:**

```bash
npm install
```

2. **Configure the service:**

Edit [config.json](config.json) to customize server settings:

```json
{
  "servers": [
    { 
      "url": "http://localhost:8628/tmf-api/performance/v5" 
    }
  ],
  "OPENAPI": "/openapi",
  "tmfid": "TMF628"
}
```

3. **Start the service:**

```bash
npm start
```

The service will start on port 8628 (configurable via environment variable `PORT`).


### Build automation and versioning

The build and release process for docker images is described here:
[/docs/developer/work-with-dockerimages.md](../../../docs/developer/work-with-dockerimages.md)


### Kubernetes Deployment

Deploy using the provided Helm chart:

```bash
helm install carbon-intensity-service ../../../charts/carbon-intensity-service
```

See the [carbon-intensity-service Helm chart](../../../charts/carbon-intensity-service/README.md) for configuration options.


### Data Management Strategies

The API supports three approaches for updating carbon intensity data:

| Method | Persistence | Use Case | Endpoint |
|--------|-------------|----------|----------|
| **File Update + Hot-reload** | Permanent | Production, scheduled updates | File modification triggers automatic reload |
| **PATCH Operation** | In-memory only | Testing, temporary overrides | `PATCH /performanceMeasurement/{id}` |
| **Manual Reload** | Loads from file | Discard in-memory changes | `POST /admin/reload` |

## API Endpoints Summary

| Method | Endpoint | Description | Standard |
|--------|----------|-------------|----------|
| GET | `/performanceMeasurement` | List carbon intensity measurements | TMF628 |
| GET | `/performanceMeasurement/{id}` | Get measurement by ID | TMF628 |
| PATCH | `/performanceMeasurement/{id}` | Update measurement (in-memory) | Extended |
| POST | `/admin/reload` | Reload data from file | Admin |
| GET | `/admin/stats` | Get data statistics | Admin |
| GET | `/` | Service status | Info |
| GET | `/hello` | Health check | Info |
| GET | `/api-docs` | Swagger UI | Docs |
| GET | `/openapi` | OpenAPI specification | Docs |

## Logging

The service uses Winston for structured logging. Log messages include:

- Incoming request details (method, path, URL)
- Query parameter values
- Data filtering and transformation steps
- File reload events
- Error conditions with stack traces

**Example log output:**

```
info: TMF628 Performance Management basePath: /tmf-api/performance/v5
info: Data loaded from carbon-intensity-data.json: 48 records
info: File watching enabled for real-time data updates
info: Watching file for changes: carbon-intensity-data.json
info: Express server listening on port 8628
info: Request: GET /tmf-api/performance/v5/performanceMeasurement - URL: /tmf-api/performance/v5/performanceMeasurement?region=us-central1-c
info: listPerformanceMeasurement: total 48 measurements
info: Received parameters: validForTimestamp=undefined, region=us-central1-c
info: Filtered by region us-central1-c: 48 measurements
```

## Related Resources

- **Helm Chart**: [charts/carbon-intensity-service](../../charts/carbon-intensity-service/)
- **Carbon Management Operator**: [charts/carbon-management-operator](../../charts/carbon-management-operator/)
- **TMF628 Specification**: [TMF Forum Performance Management API](https://www.tmforum.org/resources/specification/tmf628-performance-management-api-rest-specification-r19-5-0/)
- **ODA Canvas**: [ODA Canvas Repository](../../README.md)
