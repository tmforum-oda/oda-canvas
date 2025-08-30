# The 'business stakeholders' for the canvas Behaviour Driven Design are the Engineering teams
# from the Vendor of a component, from a Systems Integrator who may be integrating and deploying 
# a component, or a Service Provider's Operations team who may be supporting a component.

@UC017         # tagged as use case 17 (PDB Management)
@UC017-F002    # tagged as feature 2 within use case 17
Feature: UC017-F002 PDB Management - Policy Based

    Background:
        Given the PDB Management Operator is deployed in the 'canvas' namespace
        And the operator is running and ready

    Scenario Outline: Apply AvailabilityPolicy to deployments
        Given an AvailabilityPolicy '<PolicyName>' with enforcement mode '<EnforcementMode>'
        And the policy targets deployments with label '<LabelSelector>'
        And the policy specifies '<PolicyMinAvailable>' as minAvailable
        When I create a deployment '<DeploymentName>' with '<Replicas>' replicas
        And the deployment has label '<LabelKey>' set to '<LabelValue>'
        And the PDB operator processes the deployment
        Then a PDB named '<DeploymentName>-pdb' should be created
        And the PDB should have '<ExpectedMinAvailable>' as minAvailable

    Examples:
    | PolicyName        | EnforcementMode | LabelSelector           | PolicyMinAvailable | DeploymentName | Replicas | LabelKey    | LabelValue  | ExpectedMinAvailable |
    | production-policy | strict          | environment=production  | 90%                | prod-app       | 5        | environment | production  | 90%                  |
    | staging-policy    | flexible        | environment=staging     | 75%                | staging-app    | 3        | environment | staging     | 75%                  |
    | dev-policy        | advisory        | environment=development | 50%                | dev-app        | 2        | environment | development | 50%                  |

    Scenario: Policy priority resolution
        Given an AvailabilityPolicy 'high-priority' with priority '100'
        And the policy targets deployments with label 'tier=critical'
        And the policy specifies '90%' as minAvailable
        And an AvailabilityPolicy 'low-priority' with priority '50'
        And the policy targets deployments with label 'tier=critical'
        And the policy specifies '75%' as minAvailable
        When I create a deployment 'critical-app' with '6' replicas
        And the deployment has label 'tier' set to 'critical'
        And the PDB operator processes the deployment
        Then a PDB named 'critical-app-pdb' should be created
        And the PDB should have '90%' as minAvailable
        And the PDB should reference policy 'high-priority'

    Scenario: Strict enforcement mode validation
        Given an AvailabilityPolicy 'strict-policy' with enforcement mode 'strict'
        And the policy targets deployments with label 'require-pdb=true'
        And the policy specifies '75%' as minAvailable
        When I create a deployment 'must-have-pdb' with '3' replicas
        And the deployment has label 'require-pdb' set to 'true'
        But the deployment does not have availability annotations
        And the PDB operator processes the deployment
        Then a PDB named 'must-have-pdb-pdb' should be created
        And the PDB should have '75%' as minAvailable
        And the webhook should enforce the policy requirements

    Scenario: Maintenance window suspension
        Given an AvailabilityPolicy 'maintenance-policy' with maintenance window '02:00-04:00 UTC'
        And the policy targets deployments with label 'maintenance=enabled'
        And the policy specifies '75%' as minAvailable
        And a deployment 'maintenance-app' with '4' replicas exists
        And the deployment has label 'maintenance' set to 'enabled'
        And a PDB 'maintenance-app-pdb' exists with '75%' minAvailable
        When the current time is within the maintenance window
        And the PDB operator processes the maintenance window
        Then the PDB 'maintenance-app-pdb' should be suspended
        When the current time is outside the maintenance window
        And the PDB operator processes the maintenance window
        Then the PDB 'maintenance-app-pdb' should be restored with '75%' minAvailable

    Scenario: Policy deletion cleanup
        Given an AvailabilityPolicy 'temp-policy' exists
        And the policy targets deployments with label 'temp=true'
        And a deployment 'temp-app' with label 'temp=true' exists
        And a PDB 'temp-app-pdb' exists managed by 'temp-policy'
        When I delete the AvailabilityPolicy 'temp-policy'
        And the PDB operator processes the deletion
        Then the PDB 'temp-app-pdb' should be deleted
        And the operator should log the cleanup action

    Scenario: Custom PDB configuration through policy
        Given an AvailabilityPolicy 'custom-pdb-policy' with custom PDB config
        And the policy specifies minAvailable as '2' absolute value
        And the policy specifies unhealthyPodEvictionPolicy as 'IfHealthyBudget'
        And the policy targets deployments with label 'custom=true'
        When I create a deployment 'custom-app' with '5' replicas
        And the deployment has label 'custom' set to 'true'
        And the PDB operator processes the deployment
        Then a PDB named 'custom-app-pdb' should be created
        And the PDB should have '2' as minAvailable absolute value
        And the PDB should have unhealthyPodEvictionPolicy set to 'IfHealthyBudget'

    Scenario: Flexible enforcement allows higher availability class
        Given an AvailabilityPolicy 'flex-policy' with enforcement mode 'flexible'
        And the policy specifies 'standard' as minimumClass
        And the policy specifies 'high-availability' as availabilityClass
        And the policy targets deployments with label 'flex=true'
        When I create a deployment 'flex-upgrade' with '5' replicas
        And the deployment has label 'flex' set to 'true'
        And the deployment has annotation 'oda.tmforum.org/availability-class' set to 'mission-critical'
        And the PDB operator processes the deployment
        Then a PDB named 'flex-upgrade-pdb' should be created
        And the PDB should have '90%' as minAvailable

    Scenario: Advisory enforcement with override reason
        Given an AvailabilityPolicy 'advisory-strict' with enforcement mode 'advisory'
        And the policy requires override reason
        And the policy specifies 'high-availability' as availabilityClass
        And the policy targets deployments with label 'advisory=true'
        When I create a deployment 'advisory-test' with '4' replicas
        And the deployment has label 'advisory' set to 'true'
        And the deployment has annotation 'oda.tmforum.org/availability-class' set to 'non-critical'
        And the deployment has annotation 'oda.tmforum.org/override-reason' set to 'Development testing only'
        And the PDB operator processes the deployment
        Then a PDB named 'advisory-test-pdb' should be created
        And the PDB should have '25%' as minAvailable
        And the operator should log the override reason