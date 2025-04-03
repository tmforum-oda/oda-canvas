
# Installing and executing the BDD tests


To execute the tests, first you install the necessary packages and set the environment variables.

- install necessary packages

  ```bash
  cd identity-manager-utils-keycloak
  npm install
  cd ../package-manager-utils-helm
  npm install
  cd ../resource-inventory-utils-kubernetes
  npm install
  cd ..
  npm install
  ```

- create a `.env` file and set `KEYCLOAK_USER`, `KEYCLOAK_PASSWORD`, `KEYCLOAK_BASE_URL` and `KEYCLOAK_REALM`, - or use another option to define the variables

  ```
  KEYCLOAK_USER=admin 
  KEYCLOAK_PASSWORD=adpass 
  KEYCLOAK_BASE_URL=http://localhost:8083/auth/
  KEYCLOAK_REALM=odari
  ```

- Fetched the list of pods from canvas namespace

kubectl get pods -n canvas 

-Run Kubernetes command to forward a local port on your machine (port 8083) to a specific port (also 8083) on a pod (canvas-keycloak-0) in the canvas namespace.

kubectl port-forward pods/canvas-keycloak-0 8083:8083 -n canvas

Let it run, so open another terminal from “feature-definition-and-test-kit” folder

- Export the environment values to load them in the shell

export $(cat .env)


## How to run the tests

Run the test in the command line using the following command:

```bash
npm start
```

All the tests should run and display the results in the command line.

If you only want to run a single test, you can use the following command:

```
npm start -- features/UC003-F001-Expose-APIs-Create-API-Resource.feature
```

The use cases and features are tagged. You can run the tests for a given use case with the following command:

```
npm start -- --tags '@UC003'
```

Or run the tests for a single feature with the following command:

```
npm start -- --tags '@UC003-F001'
```

## Updating the master test status


To update the master test status that appears in the top-level [README.md](../README.md), set the following environment variable:

- set or export `CUCUMBER_PUBLISH_TOKEN` 
  
  ```
  CUCUMBER_PUBLISH_TOKEN=9afda79b-9ea0-44ff-8359-7f381ade4bb6
  ```
- run 'npm start' command to execute all the tests