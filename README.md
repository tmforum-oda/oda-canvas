# Open Digital Architecture Canvas

[![Supported-component-version](https://img.shields.io/badge/dynamic/yaml?url=https%3A%2F%2Fraw.githubusercontent.com%2Ftmforum-oda%2Foda-canvas%2Fmaster%2Fcharts%2Fcanvas-oda%2FChart.yaml&query=%24.appVersion&label=Supported-component-version)](https://github.com/tmforum-oda/oda-canvas)
[![Canvas-version](https://img.shields.io/badge/dynamic/yaml?url=https%3A%2F%2Fraw.githubusercontent.com%2Ftmforum-oda%2Foda-canvas%2Fmaster%2Fcharts%2Fcanvas-oda%2FChart.yaml&query=%24.version&label=Canvas-version)](https://github.com/tmforum-oda/oda-canvas)
[![License](https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fraw.githubusercontent.com%2Ftmforum-oda%2Foda-canvas-ctk%2Fmain%2Fpackage.json&query=%24.license&label=License&color=%09%23a3ff00)](https://github.com/tmforum-oda/oda-canvas/blob/master/LICENSE)

[![BDD-passed](https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fmessages.cucumber.io%2Fapi%2Freport-collections%2Ff62e87a7-f6bf-4aaf-b603-d4fa2b05b630%2Freports&query=%24.reports%5B-1%3A%5D.statusCounts.PASSED&prefix=Passed%3A%20&style=flat-square&label=BDD-and-TDD%20tests%20&color=%230BDA51)](https://reports.cucumber.io/report-collections/f62e87a7-f6bf-4aaf-b603-d4fa2b05b630)[![undefined](https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fmessages.cucumber.io%2Fapi%2Freport-collections%2Ff62e87a7-f6bf-4aaf-b603-d4fa2b05b630%2Freports&query=%24.reports%5B-1%3A%5D.statusCounts.UNDEFINED&prefix=Undefined%3A%20&style=flat-square&label=%20&color=%23FFC000)](https://reports.cucumber.io/report-collections/f62e87a7-f6bf-4aaf-b603-d4fa2b05b630)[![failed](https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fmessages.cucumber.io%2Fapi%2Freport-collections%2Ff62e87a7-f6bf-4aaf-b603-d4fa2b05b630%2Freports&query=%24.reports%5B-1%3A%5D.statusCounts.FAILED&prefix=Failed%3A%20&style=flat-square&label=%20&color=%23D22B2B)](https://reports.cucumber.io/report-collections/f62e87a7-f6bf-4aaf-b603-d4fa2b05b630)








The Open Digital Architecture (ODA) Canvas is an execution environment for ODA Components and the release automation part of a CI/CD pipeline. This repository contains the Reference Implementation, open-source code, use-cases and compliance-test-kit for a [TMForum ODA canvas](https://www.tmforum.org/oda/deployment-runtime/oda-canvas/). 


You are free to use this as a starting point for your own ODA Canvas implementation. The [Usecase Library](usecase-library/README.md) shows how ODA Components interact with the ODA Canvas. The [Compliance Test Kit](compliance-test-kit/README.md) details the features required to be a fully compliant ODA Canvas and a set of compliance tests that can be used to validate any ODA Canvas. The [source code](source/README.md) contains the source code for the operators that are part of the ODA Canvas.

The Reference Implementation of the ODA Canvas will be used for ODA Component certification. 



## Installation

see [Installation Guide](installation/README.md) for installation instructions.


## ODA Canvas Design

The design (including ongoing work) of the ODA Canvas is documented in [ODA Canvas Design](Canvas-design.md).


## Release notes

| Version    | Release notes                         |
|:----------:|---------------------------------------|
| 1.1.0      | Added support for multiple specifications of each Open-API. The v1beta3 `exposedAPI` object defines its `specification` property as an array. This is specifically designed to allow TM Forum Gen5 Open-APIs (which can be specified alongside Gen4 APIs).  <BR/> The [Webhook](./source/webhooks) will automatically convert v1beta2 and v1beta1 specifications to v1beta3 with an array of 1.          |
| 1.0.0      | First tracked release for component version v1beta3 (also supports N-2 versions i.e. v1beta2 and v1beta1).

