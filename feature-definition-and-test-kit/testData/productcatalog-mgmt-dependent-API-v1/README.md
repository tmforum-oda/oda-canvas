# Product Catalog Management Component - Management DependentAPI Test Package

This is a test package for the ODA Canvas Component Operator that includes a DependentAPI in the managementFunction segment.

This package is used to test that the component-operator correctly creates DependentAPI resources for the managementFunction segment.

## Features

- Product Catalog API (TMF620) in coreFunction
- Metrics API in managementFunction with exposedAPI
- DependentAPI for downstream Resource Catalog service (TMF634) in managementFunction
- Party Role API (TMF669) in securityFunction

## Usage

This package is used in the Canvas Test Kit (CTK) BDD tests to validate the component-operator's ability to handle DependentAPIs in different component segments.
