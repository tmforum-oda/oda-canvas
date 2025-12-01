# ODA Canvas Features and Test Kit

The ODA Canvas takes a Behaviour Driven Design (BDD) approch to define the features of the canvas. BDD allows you to specify the desired behavior of software through examples in plain language that both business stakeholders and technical teams can understand. These examples are written in a format known as Gherkin, which uses Given-When-Then syntax to describe test scenarios.

* **Given:** This part of the syntax sets the scene for the scenario. It describes the initial context or the pre-conditions of the system before the key action is performed. 
Example: "Given the user is logged into their account"
* **When:**
This section describes the event or the action that triggers the scenario. It is the key action that the user performs or the event that occurs within the system.
Example: "When the user clicks on the delete account button"
* **Then:**
This final part specifies the expected outcome or the post-conditions following the action described in the When section. It clearly defines what success (or sometimes failure) looks like.
Example: "Then the user's account is deactivated and the user is redirected to the homepage"

By defining the desired behavior of the software through examples, you can then implement automated tests to verify that the software behaves as expected. This approach helps to ensure that the software meets the requirements of the business and that it continues to do so as it evolves over time. The automated tests are written in step definitions that map the plain language examples to code that interacts with the software under test.

## Linkage to use-cases

Each BDD feature is linked to the respective use-case in the [use-case library](../usecase-library/README.md). The use-case provides the context and details for the feature. This linkage ensures that the features and are aligned with the overall design of the ODA Canvas and that the tests are verifying the correct behavior.

## Work breakdown

For contributors contributing new features to the ODA Canvas, the expectation is that the contibuitor will define the features alongside implementing the software. Instead of having separate design, development and test teams, the approach is to separate work into different features and have the same contributor (or small team) work on the feature from design to implementation to testing. This approach is known as feature-driven development and is a key part of the agile methodology.



## List of BDD Features

The list below shows the features organized by use case, with their current test status indicated. ✅ indicates the corresponding test is ready, ⏳ indicates the test has yet to be defined.

### UC002 - Manage Components

* ✅ [F001 - Install Component](features/UC002-F001-Install-Component.feature)
* ✅ [F002 - Upgrade Component](features/UC002-F002-Upgrade-Component.feature)
* ✅ [F003 - Install Component from Reference Examples](features/UC002-F003-Install-Component-from-reference-examples.feature)
* ✅ [F004 - Uninstall Component from Reference Examples](features/UC002-F004-Uninstall-Component-from-reference-examples.feature)
* ✅ [F005 - Install Component into Other Namespace](features/UC002-F005-Install-Component-into-other-namespace.feature)
* ✅ [F006 - Uninstall Component from Other Namespace](features/UC002-F006-Uninstall-Component-from-other-namespace.feature)

### UC003 - Expose APIs for Component
* ✅ [F001 - Create API Resource](features/UC003-F001-Expose-APIs-Create-API-Resource.feature)
* ✅ [F002 - Publish API Resource URL](features/UC003-F002-Expose-APIs-Publish-API-Resource-URL.feature)
* ✅ [F003 - Verify API implementation is ready](features/UC003-F003-Expose-APIs-Verify-API-implementation-is-ready.feature)
* ✅ [F004 - Upgrade component with additional API](features/UC003-F004-Expose-APIs-Upgrade-component-with-additional-API.feature)
* ✅ [F005 - Upgrade component with removed API](features/UC003-F005-Expose-APIs-Upgrade-component-with-removed-API.feature)
* ✅ [F006 - Component Specified Rate Limiting and Throttling of API Requests](features/UC003-F006-Expose-APIs-Component-Specified-Rate-Limiting-and-Throttling-of-API-Requests.feature)

### UC005 - Configure Users and Roles
* ✅ [F001 - Apply Standard Defined Role to Canvas Admin client](features/UC005-F001-Bootstrap-Apply-Standard-Defined-Role-to-Canvas-Admin-client.feature)
* ✅ [F002 - Add Permission Specification Sets in Component to Identity Platform](features/UC005-F002-Bootstrap-Add-Permission-Specification-Sets-in-Component-to-Identity-Platform.feature)
* ✅ [F003 - Add Static Roles From Component to Identity Platform](features/UC005-F003-Bootstrap-Add-Static-Roles-From-Component-to-Identity-Platform.feature)

### UC007 - Dependent APIs
* ✅ [F001 - Create Dependent API Resource](features/UC007-F001-Dependent-APIs-Create-Dependent-API-Resource.feature)
* ✅ [F002 - Configure Dependent API Single Downstream](features/UC007-F002-Dependent-APIs-Configure-Dependent-APIs-Single-Downstream.feature)

### UC010 - Authentication External
* ⏳ [F001 - Logging and Monitoring of Authentication Activity](features/UC010-F001-External-Authentication-Logging-and-Monitoring-of-Authentication-Activity.feature)

### UC012 - View Business Observability
* ⏳ [F001 - View Functional Observability](features/UC012-F001-View-Functional-Observability.feature)

### UC013 - Seamless upgrade
* ✅ [F001 - Installing components using prev version](features/UC013-F001-Seamless-upgrades-Installing-components-using-prev-version.feature)
* ✅ [F002 - Canvas Operators using prev version](features/UC013-F002-Seamless-upgrades-Canvas-Operators-using-prev-version.feature)

### UC015 - API Gateway configuration
* ✅ [F001 - Create Apisix Api Gateway Route](features/UC015-F001-Create-ApisixApiGateway-Route.feature)
* ✅ [F002 - Create Kong Api Gateway Route](features/UC015-F002-Create-KongApiGateway-Route.feature)
* ✅ [F003 - Create Apisix Api Gateway Plugin](features/UC015-F003-Create-ApisixApiGateway-Plugin.feature)
* ✅ [F004 - Create Kong Api Gateway Plugin](features/UC015-F004-Create-KongApiGateway-Plugin.feature)




## Executing the BDD tests

Follow the instructions in [executing tests](Executing-tests.md) to run the BDD tests.

When you run the tests, the test results are reported in the console and in a HTML report. The console output is shown below:

![CTK Console Output](images/CTK-console-output.png)

And the cucumber report will look like this:

![CTK Cucumber report](images/CTK-cucumber-report.png)

## Test Implementation

The BDD tests in this kit are designed with a layered architecture that separates test logic from implementation-specific details, ensuring the tests remain portable and maintainable across different Canvas implementations.

### Step Definitions

The heart of the test execution lies in the step definition files, located in the `features/step-definition/` directory. These files contain JavaScript functions that map the natural language steps in the Gherkin feature files to executable code. Each step definition:

- **Parses Gherkin syntax**: Converts "Given", "When", and "Then" statements into actionable test code
- **Maintains test state**: Manages context and data flow between test steps
- **Calls utility functions**: Delegates implementation-specific operations to utility modules
- **Performs assertions**: Validates expected outcomes against actual results

The step definitions act as a translation layer between the business-readable feature descriptions and the technical test implementation, ensuring that the test logic remains clear and focused on the Canvas behavior being verified.

### Implementation Agnostic Design

The test framework is deliberately designed to be implementation agnostic, meaning the same test suite can validate different Canvas implementations (e.g., different Kubernetes distributions, cloud providers, or deployment configurations). This is achieved through:

- **Abstracted interactions**: Step definitions use high-level function calls rather than direct API calls
- **Configurable endpoints**: Test targets are defined through configuration rather than hard-coded values
- **Standardized interfaces**: All Canvas implementations must expose the same ODA-compliant interfaces

### Utilities Layer

The implementation-specific code resides in utility files within the `utilities/` directory. These utilities handle:

- **Environment setup**: Configuring test environments and prerequisites
- **API interactions**: Making HTTP requests to Canvas endpoints and Kubernetes APIs
- **Resource management**: Creating, updating, and cleaning up test resources
- **Data parsing**: Processing responses and extracting relevant information
- **Configuration handling**: Managing environment-specific settings and credentials

By isolating implementation details in the utilities layer, the test framework can be easily adapted to different Canvas deployments by simply updating the utility functions while keeping the core test logic unchanged.

### Test Execution Flow

1. **Feature parsing**: Cucumber reads the `.feature` files and identifies scenarios to execute
2. **Step matching**: Each Gherkin step is matched to its corresponding step definition function
3. **Utility delegation**: Step definitions call appropriate utility functions for implementation-specific operations
4. **Result validation**: Assertions verify that the Canvas behavior matches the expected outcomes
5. **Reporting**: Results are aggregated and presented in both console output and HTML reports

This architecture ensures that the test kit can serve as a comprehensive compliance validation tool for any ODA Canvas implementation while maintaining readability and maintainability of the test suite.


