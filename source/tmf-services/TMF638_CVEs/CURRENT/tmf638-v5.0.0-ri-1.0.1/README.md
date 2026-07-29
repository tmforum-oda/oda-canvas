# TM Forum Open API – Reference Implementation (RI)

This is a **Reference Implementation (RI)** for simulating a TM Forum Open API and understanding the API. 

It is based on the OpenAPI specification and can be used to **mock the behaviour** of the API when a real implementation is not yet available.

This is ideal for:
- Testing client applications early in development
- Frontend/backend decoupling
- Contract-based integration validation
- Viewing a sunny-day result

## Prerequisites

- **Docker Desktop** is installed and running.
- On **Windows 11**, ensure:
  - Virtualization is enabled in BIOS
  - WSL 2 is installed and set as default

Make sure the folder includes:
-  'docker-compose.yaml'
-  `run.sh` or `run.bat` (launcher scripts)


## Start the Reference Implementation

### Linux/macOS:
```bash
chmod +x run.sh
./run.sh
```

### Windows:
```cmd
run.bat
```

Once started, the service will simulate the API and respond to incoming requests.

## View and test the API

You can browse the API documentation and test available endpoints. 

```
Open: `http://localhost:8[api-number]/tmf-api/partyRoleManagement/v5/api-docs/`
```


You can now make HTTP requests to this address using:
- Postman
- curl
- Any API client or application under development

The RI will generate **mock responses** based on the API contract and conformance profile, ensuring that the behaviour is predictable and spec-compliant.


## Investigation features

- **Resetting the RI:** The RI contains a database so the CTK can link REST operations and execute more meaningful tests. Each time a test suite is run, the CTK resets the RI’s database by calling the tmf-ri-admin/v1/clear-all-data endpoint in the RI.

It is also possible to call this feature from Postman or by using a curl command, for example:
```
   curl -X  DELETE 'http://127.0.0.1:8635/tmf-ri-admin/v1/clear-all-data'
```
The base URL and port (127.0.0.1:8635) depend on your system configuration.

Alternatively, if you would like this feature on your system, please implement this endpoint. 

Please note that if your system has not implemented this endpoint, the CTK will ignore the 404 response.

## Troubleshooting

- **Resetting the RI:** In some cases, it can be benefical to reset the Docker container for the RI. This can be done by simply running the 
cleanup script.

### Linux/macOS:
```bash
chmod +x cleanup.sh
./cleanup.sh
```

### Windows:
```cmd
cleanup.bat
```


## Questions?

Contact: [openapi@tmforum.org](mailto:openapi@tmforum.org)

