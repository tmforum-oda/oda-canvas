# Product Catalog Management Component - Security DependentAPI Test Package

This is a test package for the ODA Canvas Component Operator that includes a DependentAPI in the securityFunction segment.

This package is used to test that the component-operator correctly creates DependentAPI resources for the securityFunction segment.

## Features

- Product Catalog API (TMF620) in coreFunction
- Metrics API in managementFunction
- User Role Permission API (TMF672) in securityFunction with exposedAPI
- DependentAPI for downstream user role permissions service in securityFunction

## Usage

This package is used in the Canvas Test Kit (CTK) BDD tests to validate the component-operator's ability to handle DependentAPIs in different component segments.
