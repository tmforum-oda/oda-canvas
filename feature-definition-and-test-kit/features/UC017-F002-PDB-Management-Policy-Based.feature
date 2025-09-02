# The 'business stakeholders' for the canvas Behaviour Driven Design are the Engineering teams
# from the Vendor of a component, from a Systems Integrator who may be integrating and deploying 
# a component, or a Service Provider's Operations team who may be supporting a component.

@UC017         # tagged as use case 17 (PDB Management)
@UC017-F002    # tagged as feature 2 within use case 17
Feature: UC017-F002 PDB Management - Policy Based

    Background:
        Given the PDB Management Operator is deployed in the 'canvas' namespace
        And the operator is running and ready

    Scenario Outline: Test AvailabilityPolicy enforcement modes
        Given an AvailabilityPolicy '<PolicyName>' with enforcement mode '<EnforcementMode>'
        And the policy targets deployments with label '<LabelSelector>'
        And the policy specifies '<PolicyClass>' availability class
        When I create a deployment '<DeploymentName>' with '<Replicas>' replicas
        And the deployment has label '<LabelKey>' set to '<LabelValue>'
        And the deployment has annotation 'oda.tmforum.org/availability-class' set to '<AnnotationClass>'
        And the PDB operator processes the deployment
        Then a PDB named '<DeploymentName>-pdb' should be created
        And the PDB should have '<ExpectedMinAvailable>' as minAvailable

    Examples:
    | PolicyName        | EnforcementMode | LabelSelector           | PolicyClass       | DeploymentName | Replicas | LabelKey    | LabelValue  | AnnotationClass   | ExpectedMinAvailable |
    | production-policy | strict          | environment=production  | mission-critical  | prod-app       | 5        | environment | production  | standard          | 90%                  |
    | staging-policy    | flexible        | environment=staging     | high-availability | staging-app    | 3        | environment | staging     | mission-critical  | 90%                  |
    | dev-policy        | advisory        | environment=development | standard          | dev-app        | 2        | environment | development | non-critical      | 20%                  |

    Scenario: Policy priority resolution with strict enforcement
        Given an AvailabilityPolicy 'high-priority' with priority '100'
        And the policy targets deployments with label 'tier=critical'
        And the policy specifies 'mission-critical' availability class
        And the policy has enforcement mode 'strict'
        And an AvailabilityPolicy 'low-priority' with priority '50'
        And the policy targets deployments with label 'tier=critical'
        And the policy specifies 'high-availability' availability class
        And the policy has enforcement mode 'strict'
        When I create a deployment 'critical-app' with '6' replicas
        And the deployment has label 'tier' set to 'critical'
        And the deployment has annotation 'oda.tmforum.org/availability-class' set to 'standard'
        And the PDB operator processes the deployment
        Then a PDB named 'critical-app-pdb' should be created
        And the PDB should have '90%' as minAvailable

    Scenario: Strict enforcement ignores annotations
        Given an AvailabilityPolicy 'strict-policy' with enforcement mode 'strict'
        And the policy targets deployments with label 'require-pdb=true'
        And the policy specifies 'high-availability' availability class
        When I create a deployment 'must-have-pdb' with '3' replicas
        And the deployment has label 'require-pdb' set to 'true'
        And the deployment has annotation 'oda.tmforum.org/availability-class' set to 'non-critical'
        And the PDB operator processes the deployment
        Then a PDB named 'must-have-pdb-pdb' should be created
        And the PDB should have '75%' as minAvailable

    Scenario: Flexible enforcement with minimum class
        Given an AvailabilityPolicy 'flex-policy' with enforcement mode 'flexible'
        And the policy targets deployments with label 'flex=true'
        And the policy specifies 'high-availability' availability class
        And the policy has minimum class 'standard'
        When I create a deployment 'flex-app' with '4' replicas
        And the deployment has label 'flex' set to 'true'
        And the deployment has annotation 'oda.tmforum.org/availability-class' set to 'non-critical'
        And the PDB operator processes the deployment
        Then a PDB named 'flex-app-pdb' should be created
        And the PDB should have '50%' as minAvailable

    Scenario: Advisory enforcement allows annotation override
        Given an AvailabilityPolicy 'advisory-policy' with enforcement mode 'advisory'
        And the policy targets deployments with label 'advisory=true'
        And the policy specifies 'high-availability' availability class
        When I create a deployment 'advisory-app' with '3' replicas
        And the deployment has label 'advisory' set to 'true'
        And the deployment has annotation 'oda.tmforum.org/availability-class' set to 'standard'
        And the PDB operator processes the deployment
        Then a PDB named 'advisory-app-pdb' should be created
        And the PDB should have '50%' as minAvailable

    Scenario: Policy with custom availability class
        Given an AvailabilityPolicy 'custom-policy' with custom PDB config
        And the policy specifies minAvailable as '2' absolute value
        And the policy targets deployments with label 'custom=true'
        And the policy has enforcement mode 'strict'
        When I create a deployment 'custom-app' with '5' replicas
        And the deployment has label 'custom' set to 'true'
        And the deployment has annotation 'oda.tmforum.org/availability-class' set to 'standard'
        And the PDB operator processes the deployment
        Then a PDB named 'custom-app-pdb' should be created
        And the PDB should have '2' as minAvailable absolute value

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
        And the PDB should have '20%' as minAvailable
        And the operator should log the override reason