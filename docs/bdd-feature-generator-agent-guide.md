# BDD Feature Generator Custom Agent - Usage Guide

## Overview

The `bdd-feature-generator` custom agent is a specialized GitHub Copilot agent designed to create BDD (Behavior-Driven Development) feature files and test automation for the TM Forum ODA Canvas project. It follows all established conventions and ensures consistency across the test suite.

## Location

**Agent Profile**: [.github/agents/bdd-feature-generator.agent.md](.github/agents/bdd-feature-generator.agent.md)

## What It Does

The agent automatically:
1. ✅ Creates properly formatted Gherkin feature files with correct naming and structure
2. ✅ Generates JavaScript step definition stubs (only when needed)
3. ✅ Updates `feature-definition-and-test-kit/README.md` with new feature entries
4. ✅ Reuses existing step definitions to avoid duplication
5. ✅ Follows ODA Canvas naming conventions and patterns
6. ✅ Links features to use case documentation

## How to Use

### Accessing the Agent

**In GitHub.com**:
- Open the Copilot panel or agent tab
- Select `@bdd-feature-generator` from available agents
- Provide your request

**In VS Code**:
- Open GitHub Copilot Chat
- Use `@bdd-feature-generator` to invoke the agent
- The agent has access to read, edit, and search tools

**In GitHub CLI**:
```bash
gh copilot suggest --agent bdd-feature-generator "your request here"
```

### Example Requests

#### 1. Create a New Feature from Scratch

```
@bdd-feature-generator Create a BDD feature for UC008-F001 that tests 
configuring subscribed events on a component. The component should receive 
notifications when events occur.
```

**What the agent will do**:
- Read UC008 use case documentation
- Create `UC008-F001-Configure-Subscribed-Events-Create-Event-Resource.feature`
- Check existing step definitions for reusable patterns
- Create new step definitions only if needed
- Update README.md with the new feature entry

#### 2. Add Scenarios to Existing Feature

```
@bdd-feature-generator Add a scenario to UC002-F001-Install-Component.feature 
that tests installing a component with custom configuration values.
```

**What the agent will do**:
- Read the existing feature file
- Add a new scenario following established patterns
- Identify if new step definitions are needed
- Update the feature file without breaking existing scenarios

#### 3. Generate Step Definitions for New Steps

```
@bdd-feature-generator I have a new Given step "Given a component with encrypted 
secrets configured" that needs implementation. Create the step definition stub 
in the appropriate file.
```

**What the agent will do**:
- Search existing step definition files to avoid duplication
- Determine the correct file to add the step (likely `ComponentManagementSteps.js` or `IdentityManagementSteps.js`)
- Generate a properly formatted step definition with JSDoc
- Use appropriate utility libraries

#### 4. Create Feature from Use Case

```
@bdd-feature-generator Review UC012-F003 in the use case library and create 
a complete BDD feature file with all necessary scenarios.
```

**What the agent will do**:
- Read the use case documentation
- Create feature file with appropriate scenarios
- Generate Examples tables for parameterized tests
- Map to existing or create new step definitions
- Update README.md

#### 5. Update README for New Feature

```
@bdd-feature-generator I've manually created UC015-F005-Create-Istio-Gateway-Route.feature. 
Please update the README.md to include this feature in the UC015 section.
```

**What the agent will do**:
- Find the UC015 section in README.md
- Add the new feature entry with ⏳ status
- Maintain proper ordering and formatting

## What the Agent Knows

### ODA Canvas Architecture
- Component management and lifecycle
- API exposure and dependent API configuration
- Identity management with Keycloak
- Observability and monitoring setup
- API Gateway configurations (Apisix, Kong)
- Kubernetes resource management

### Existing Test Patterns
- Component installation/upgrade/uninstall workflows
- API resource creation and verification
- Identity and role management
- Event subscription and publication
- PodDisruptionBudget management
- Gateway route and plugin configuration

### Available Test Data
- `productcatalog-v1` - Standard product catalog component
- `productcatalog-dependendent-API-v1` - With dependent APIs
- `productcatalog-dynamic-roles-v1` - With dynamic roles
- `productinventory-v1` - Inventory component
- And more in `feature-definition-and-test-kit/testData/`

### Utility Libraries
- `resource-inventory-utils-kubernetes` - K8s resource operations
- `package-manager-utils-helm` - Helm chart management
- `identity-manager-utils-keycloak` - Keycloak integration
- `component-utils` - ODA Component operations
- `observability-utils-kubernetes` - Monitoring configuration

## Tips for Best Results

### Be Specific
❌ "Create a test for APIs"
✅ "Create UC003-F007 to test exposing multiple APIs with different rate limits in the same component"

### Reference Use Cases
✅ "Based on UC007-Configure-Dependent-APIs.md, create F003 that tests multiple downstream API dependencies"

### Specify Expected Behavior
✅ "Create a scenario that verifies the component deployment status changes to 'Complete' within 10 minutes after installation"

### Indicate Test Data Preferences
✅ "Use the productcatalog-v1 package and test both coreFunction and managementFunction segments"

## Agent Capabilities

### ✅ What It Can Do
- Create complete feature files with proper structure
- Generate Scenario Outlines with Examples tables
- Reuse existing step definitions intelligently
- Create new step definitions when necessary
- Update README.md automatically
- Follow all naming conventions
- Link features to use cases
- Use appropriate test data packages

### ⚠️ What to Review
- Verify the feature logic matches your intent
- Check that Examples tables cover edge cases
- Ensure step definitions are in the correct file
- Validate timeout values for async operations
- Confirm the use case mapping is correct

### ❌ What It Won't Do
- Execute or run the tests (use `npm start` for that)
- Modify use case documentation
- Change existing test data packages
- Alter operator source code
- Modify utility library implementations

## File Structure

After using the agent, you'll typically see changes in:

```
feature-definition-and-test-kit/
├── README.md                          # Updated with new feature
├── features/
│   ├── UC{n}-F{n}-{Title}.feature    # New or modified feature file
│   └── step-definition/
│       ├── ComponentManagementSteps.js    # May contain new steps
│       ├── APIManagementSteps.js          # May contain new steps
│       └── {New}Steps.js                  # New file if needed
├── testData/                          # Reference only, not modified
└── utilities/                         # Reference only, not modified
```

## Validation

After the agent creates files, validate them:

### Feature File Validation
```bash
# Check Gherkin syntax
cd feature-definition-and-test-kit
npm test -- features/UC{number}-F{number}-*.feature
```

### Step Definition Validation
```bash
# Check for undefined steps
npm start -- --dry-run
```

### Full Test Run
```bash
# Run the specific feature
npm start -- features/UC{number}-F{number}-*.feature
```

## Common Issues and Solutions

### Issue: "Step definition not found"
**Solution**: The agent may have identified an existing pattern that doesn't quite match. Review the step definition files and adjust the Gherkin step text to match existing patterns.

### Issue: "Package not found in testData"
**Solution**: The agent references existing test data packages. If you need a new package, create it manually in `testData/` first, then ask the agent to create features using it.

### Issue: "Feature already exists"
**Solution**: Specify a different feature number (F-number) or ask the agent to add scenarios to the existing feature instead.

### Issue: "Duplicate step definition"
**Solution**: The agent tries to avoid this, but if it happens, remove the duplicate and update the feature file to use the existing step.

## Best Practices

1. **Start with Use Cases**: Always have the use case documented before creating features
2. **Review Existing Features**: Check similar features for consistent patterns
3. **Incremental Development**: Create one feature at a time and test it
4. **Reuse Test Data**: Use existing packages in `testData/` when possible
5. **Clear Scenarios**: Write scenarios that clearly describe expected behavior
6. **Update Documentation**: The agent does this automatically, but verify it's correct

## Example Workflow

### Creating a Complete Feature

1. **Document the use case** (if not already done):
   ```
   Create or update usecase-library/UC014-{Title}.md
   ```

2. **Request feature creation**:
   ```
   @bdd-feature-generator Create UC014-F001 based on the UC014 use case. 
   Test that components can subscribe to multiple event types and filter 
   events by criteria. Use productcatalog-v1 as test data.
   ```

3. **Review the output**:
   - Check the feature file structure
   - Verify scenario logic
   - Review step definitions (new and reused)
   - Confirm README.md update

4. **Test the feature**:
   ```bash
   cd feature-definition-and-test-kit
   npm start -- features/UC014-F001-*.feature
   ```

5. **Update status in README**:
   Once tests pass, change ⏳ to ✅

## Support and Feedback

- **Documentation**: See [feature-definition-and-test-kit/README.md](../feature-definition-and-test-kit/README.md)
- **Test Execution**: See [feature-definition-and-test-kit/Executing-tests.md](../feature-definition-and-test-kit/Executing-tests.md)
- **Contributing**: See [CONTRIBUTING.md](../CONTRIBUTING.md)
- **Issues**: Report problems or enhancement requests via GitHub Issues

## Version Information

- **Created**: December 23, 2025
- **Agent Version**: 1.0
- **Compatible with**: GitHub Copilot Pro, Business, and Enterprise plans
- **Supported Environments**: GitHub.com, VS Code, JetBrains IDEs, GitHub CLI

---

**Ready to create high-quality BDD tests for ODA Canvas!** 🚀

Just invoke `@bdd-feature-generator` and describe what you need.
