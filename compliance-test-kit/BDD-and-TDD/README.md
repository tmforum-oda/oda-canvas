# BDD and TDD

This repository contains a list of BDD features and scenarios that describe each interaction in the use-case library by example. The features are arranged and numbered depending on the use-case they describe. 

| Use-Case            | Feature                         | Test Status |
| ------------------- | ------------------------------- | ----------- |
| [UC003 - Expose APIs for Component](../../usecase-library/UC003-Configure-Exposed-APIs.md) | [F001 - Create API Resource](features/UC003-F001-Expose-APIs-Create-API-Resource.feature) | Complete |
| [UC003 - Expose APIs for Component](../../usecase-library/UC003-Configure-Exposed-APIs.md) | [F002 - Publish API Resource URL](features/UC003-F002-Expose-APIs-Publish-API-Resource-URL.feature) | Complete |
| [UC003 - Expose APIs for Component](../../usecase-library/UC003-Configure-Exposed-APIs.md) | [F003 - Verify API implementation is ready](features/UC003-F003-Expose-APIs-Verify-API-implementation-is-ready.feature) | Complete |
| [UC003 - Expose APIs for Component](../../usecase-library/UC003-Configure-Exposed-APIs.md) | [F004 - Upgrade component with additional API](features/UC003-F004-Expose-APIs-Upgrade-component-with-additional-API.feature) | Complete |
| [UC003 - Expose APIs for Component](../../usecase-library/UC003-Configure-Exposed-APIs.md) | [F005 - Upgrade component with removed API](features/UC003-F005-Expose-APIs-Upgrade-component-with-removed-API.feature) | Complete |
| [UC003 - Expose APIs for Component](../../usecase-library/UC003-Configure-Exposed-APIs.md) | [F006 - Component Specified Rate Limiting and Throttling of API Requests](features/UC003-F006-Expose-APIs-Component-Specified-Rate-Limiting-and-Throttling-of-API-Requests.feature) | Not started |
| [UC005 - Configure Users and Roles](../../usecase-library/UC005-Configure-Users-and-Roles.md) | [F001 - Apply Standard Defined Role to Canvas Admin user](features/UC005-F001-Bootstrap-Apply-Standard-Defined-Role-to-Canvas-Admin-user.feature) | Complete |
| [UC005 - Configure Users and Roles](../../usecase-library/UC005-Configure-Users-and-Roles.md)              | [F002 - Grouping Permission Specification Sets-into Business Roles in Identity Management Solution](features/UC005-F002-Bootstrap-Grouping-Permission-Specification-Sets-into-Business-Roles-in-Identity-Management-Solution.feature) | Not started |
| [UC005 - Configure Users and Roles](../../usecase-library/UC005-Configure-Users-and-Roles.md)              | [F003 - Secure User and Role Information](features/UC005-F003-Bootstrap-Secure-User-and-Role-Information-Communication.feature) | Not started |
| [UC005 - Configure Users and Roles](../../usecase-library/UC005-Configure-Users-and-Roles.md)              | [F004 - Component Exposes Permission Specification Set Towards Canvas](features/UC005-F004-Bootstrap-Component-Exposes-Permission-Specification-Set-Towards-Canvas.feature) | Not started |
| [UC010 - Authentication external](../../usecase-library/UC010-External-Authentication.md) | [F001 - Logging and Monitoring of Authentication Activity](features/UC010-F001-External-Authentication-Logging-and-Monitoring-of-Authentication-Activity.feature) | Not started |
| [UC013 - Seamless upgrade](../../usecase-library/UC013-Upgrade-Canvas.md) | [F001 - Installing components using prev version](features/UC013-F001-Seamless-upgrades-Installing-components-using-prev-version.feature) | Complete |
| [UC013 - Seamless upgrade](../../usecase-library/UC013-Upgrade-Canvas.md) | [F002 - Canvas Operators using prev version](features/UC013-F002-Seamless-upgrades-Canvas-Operators-using-prev-version.feature) | Complete |


## Installation

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
  KEYCLOAK_BASE_URL=http://keycloack-ip:8083/auth/ 
  KEYCLOAK_REALM=myrealm
  ```

- set or export `CUCUMBER_PUBLISH_TOKEN` only applicable for master branch, when you want to run 'npm start' command for all tests
  
  ```
  CUCUMBER_PUBLISH_TOKEN=9afda79b-9ea0-44ff-8359-7f381ade4bb6
  ```

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
