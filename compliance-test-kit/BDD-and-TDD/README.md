# BDD and TDD

This repository contains a list of BDD features and scenarios that describe each interaction in the use-case library by example. The features are arranged and numbered depending on the use-case they describe. 

| Use-Case            | Feature                         | Test Status |
| ------------------- | ------------------------------- | ----------- |
| [UC001 - Bootstrap](../../usecase-library/UC001-Bootstrap-role-for-component.md)              | [F001 - Secure User and Role Information](features/UC001-F001-Bootstrap-Secure-User-and-Role-Information-Communication.feature) | Not started |
| [UC001 - Bootstrap](../../usecase-library/UC001-Bootstrap-role-for-component.md)              | [F002 - Support Standard Defined Role for Canvas Admin](features/UC001-F002-Bootstrap-Support-Standard-Defined-Role-for-Canvas-Admin.feature) | Not started |
| [UC001 - Bootstrap](../../usecase-library/UC001-Bootstrap-role-for-component.md)              | [F003 - Grouping Permission Specification Sets-into Business Roles in Identity Management Solution](features/UC001-F003-Bootstrap-Grouping-Permission-Specification-Sets-into-Business-Roles-in-Identity-Management-Solution.feature) | Not started |
| [UC001 - Bootstrap](../../usecase-library/UC001-Bootstrap-role-for-component.md)              | [F004 - Component Exposes Permission Specification Set Towards Canvas](features/UC001-F004-Bootstrap-Component-Exposes-Permission-Specification-Set-Towards-Canvas.feature) | Not started |
| [UC002 - Expose APIs for Component](../../usecase-library/UC002-Expose-APIs-for-Component.md) | [F001 - Create API Resource](features/UC002-F001-Expose-APIs-Create-API-Resource.feature) | Complete |
| [UC002 - Expose APIs for Component](../../usecase-library/UC002-Expose-APIs-for-Component.md) | [F002 - Publish API Resource URL](features/UC002-F002-Expose-APIs-Publish-API-Resource-URL.feature) | Complete |
| [UC002 - Expose APIs for Component](../../usecase-library/UC002-Expose-APIs-for-Component.md) | [F003 - Verify API implementation is ready](features/UC002-F003-Expose-APIs-Verify-API-implementation-is-ready.feature) | Complete |
| [UC002 - Expose APIs for Component](../../usecase-library/UC002-Expose-APIs-for-Component.md) | [F004 - Upgrade component with additional API](features/UC002-F004-Expose-APIs-Upgrade-component-with-additional-API.feature) | Complete |
| [UC002 - Expose APIs for Component](../../usecase-library/UC002-Expose-APIs-for-Component.md) | [F005 - Upgrade component with removed API](features/UC002-F005-Expose-APIs-Upgrade-component-with-removed-API.feature) | Complete |
| [UC002 - Expose APIs for Component](../../usecase-library/UC002-Expose-APIs-for-Component.md) | [F006 - Component Specified Rate Limiting and Throttling of API Requests](features/UC002-F006-Expose-APIs-Component-Specified-Rate-Limiting-and-Throttling-of-API-Requests.feature) | Not started |
| [UC007 - Authentication external](../../usecase-library/UC007-Authentication-external.md) | [F001 - Logging and Monitoring of Authentication Activity](features/UC007-F001-External-Authentication-Logging-and-Monitoring-of-Authentication-Activity.feature) | Not started |
| [UC016 - Seamless upgrade](../../usecase-library/UC016-Seamless-upgrade-of-component-spec.md) | [F001 - Installing components using prev version](features/UC016-F001-Seamless-upgrades-Installing-components-using-prev-version.feature) | Complete |
| [UC016 - Seamless upgrade](../../usecase-library/UC016-Seamless-upgrade-of-component-spec.md) | [F002 - Canvas Operators using prev version](features/UC016-F002-Seamless-upgrades-Canvas-Operators-using-prev-version.feature) | Complete |



## How to run the tests

Run the test in the command line using the following command:

```
npm install
npm start
```

All the tests should run and display the results in the command line.

If you only want to run a single test, you can use the following command:

```
npm start -- features/UC002-F001-Expose-APIs-Create-API-Resource.feature
```

The use cases and features are tagged. You can run the tests for a given use case with the following command:

```
npm start -- --tags '@UC002'
```

Or run the tests for a single feature with the following command:

```
npm start -- --tags '@UC002-F001'
```