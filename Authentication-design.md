# Authentication design

This document describes the design artefacts for the Authenticaiton part of the [overall ODA Canvas design](/Canvas-design.md).

## Use cases

The authentication use cases are documented in the [use case library](../usecase-library/README.md) as follows:

* [UC001-Bootstrap-role-for-component](/usecase-library/UC001-Bootstrap-role-for-component.md)
* [UC002-Expose-APIs-for-Component](/usecase-library/UC002-Expose-APIs-for-Component.md)
* [UC003-Discover-dependent-APIs-for-Component](/usecase-library/UC003-Discover-dependent-APIs-for-Component.md)
* [UC007-Authentication-external](/usecase-library/UC007-Authentication-external.md)
* [UC008-Authentication-internal](/usecase-library/UC008-Authentication-internal.md)

## BDD Features

| Use case | BDD Feature | Description | Status |
|----------|-------------|-------------| ------ |
| UC001 | [F001](/compliance-test-kit/BDD-and-TDD/features/UC001-F001-Secure-User-and-Role-Information-Communication.feature) | Secure User and Role Information Communication | Not started [Issue](https://github.com/tmforum-oda/oda-canvas/issues/79) |
| UC001 | [F002](/compliance-test-kit/BDD-and-TDD/features/UC001-F002-Support-Standard-Defined-Role-for-Canvas-Admin.feature) | Support Standard Defined Role for Canvas Admin | Not started [Issue](https://github.com/tmforum-oda/oda-canvas/issues/85) |
| UC002 | [F001](/compliance-test-kit/BDD-and-TDD/features/UC002-F001-Create-API-Resource.feature) | Create an API resource | Complete |
| UC002 | [F002](/compliance-test-kit/BDD-and-TDD/features/UC002-F002-Publish-API-Resource-URL.feature) | Publish API Resource URL | Complete |
| UC002 | [F003](/compliance-test-kit/BDD-and-TDD/features/UC002-F003-Verify-API-implementation-is-ready.feature) | Verify API implementation is ready | Complete |
| UC002 | [F004](/compliance-test-kit/BDD-and-TDD/features/UC002-F004-Upgrade-component-with-additional-API.feature) | Upgrade component with additional API | Complete |
| UC002 | [F005](/compliance-test-kit/BDD-and-TDD/features/UC002-F005-Upgrade-component-with-removed-API.feature) | Upgrade component with removed API | Complete |


