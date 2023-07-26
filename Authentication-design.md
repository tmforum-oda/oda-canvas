# Authentication design

This document describes the design artefacts for the Authentication part of the [overall ODA Canvas design](/Canvas-design.md).

## Use cases

The authentication use cases are documented in the [use case library](../usecase-library/README.md) as follows:

* [UC001-Bootstrap-role-for-component](/usecase-library/UC001-Bootstrap-role-for-component.md)
* [UC002-Expose-APIs-for-Component](/usecase-library/UC002-Expose-APIs-for-Component.md)
* [UC003-Discover-dependent-APIs-for-Component](/usecase-library/UC003-Discover-dependent-APIs-for-Component.md)
* [UC007-Authentication-external](/usecase-library/UC007-Authentication-external.md)
* [UC008-Authentication-internal](/usecase-library/UC008-Authentication-internal.md)

## BDD Features

For each use case, a set of BDD features describes the behaviour required of the Canvas, using scenarios. The goal is for a set of business-friendly pseudo-code that describes the behaviour of the Canvas, and that directly maps to compliance tests (TDD) that will test that feature. Some features are option - the compliance report will indicate which features have passed, but will not fail the compliance test for a canvas if an optional feature is not implemented.

| Use case | BDD Feature | Mandatory / Optional | Description | Status |
|----------|-------------|----------------------|-------------| ------ |
| UC001 | [F001](/compliance-test-kit/BDD-and-TDD/features/UC001-F001-Secure-User-and-Role-Information-Communication.feature) | Mandatory | Secure User and Role Information Communication | Not started [Issue #79](https://github.com/tmforum-oda/oda-canvas/issues/79) |
| UC001 | [F002](/compliance-test-kit/BDD-and-TDD/features/UC001-F002-Support-Standard-Defined-Role-for-Canvas-Admin.feature) | Mandatory | Support Standard Defined Role for Canvas Admin | Not started [Issue #85](https://github.com/tmforum-oda/oda-canvas/issues/85) |
| UC001 | [F003](/compliance-test-kit/BDD-and-TDD/features/UC001-F003-Grouping-Permission-Specification-Sets-into-Business-Roles-in-Identity-Management-Solution.feature) | Mandatory | Grouping Permission Specification Sets into Business Roles in Identity Management Solution | Not started [Issue #82](https://github.com/tmforum-oda/oda-canvas/issues/82) |
| UC001 | [F004](/compliance-test-kit/BDD-and-TDD/features/UC001-F004-Component-Exposes-Permission-Specification-Set-Towards-Canvas.feature) | Mandatory | Component Exposes Permission Specification Set Towards Canvas | Not started [Issue #81](https://github.com/tmforum-oda/oda-canvas/issues/81) |
| UC002 | [F001](/compliance-test-kit/BDD-and-TDD/features/UC002-F001-Create-API-Resource.feature) | Mandatory | Create an API resource | Complete |
| UC002 | [F002](/compliance-test-kit/BDD-and-TDD/features/UC002-F002-Publish-API-Resource-URL.feature) | Mandatory | Publish API Resource URL | Complete |
| UC002 | [F003](/compliance-test-kit/BDD-and-TDD/features/UC002-F003-Verify-API-implementation-is-ready.feature) | Mandatory | Verify API implementation is ready | Complete |
| UC002 | [F004](/compliance-test-kit/BDD-and-TDD/features/UC002-F004-Upgrade-component-with-additional-API.feature) | Mandatory | Upgrade component with additional API | Complete |
| UC002 | [F005](/compliance-test-kit/BDD-and-TDD/features/UC002-F005-Upgrade-component-with-removed-API.feature) | Mandatory | Upgrade component with removed API | Complete |
| UC002 | [F006](/compliance-test-kit/BDD-and-TDD/features/UC002-F006-Component-Specified-Rate-Limiting-and-Throttling-of-API-Requests.feature) | Optional | Component-Specified Rate Limiting and Throttling of API Requests | Not started [Issue #80](https://github.com/tmforum-oda/oda-canvas/issues/80) |
| UC007 | [F001](/compliance-test-kit/BDD-and-TDD/features/UC007-F001-Logging-and-Monitoring-of-Authentication-Activity.feature) | Mandatory | Logging and Monitoring of Authentication Activity | Not started [Issue #84](https://github.com/tmforum-oda/oda-canvas/issues/84) |


