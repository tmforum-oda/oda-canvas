# The 'business stakeholders' for the canvas Behaviour Driven Design are the Engineering teams
# from the Vendor of a component, from a Systems Integrator who may be integrating and deploying 
# a component, or a Service Provider's Operations team who may be supporting a component.

@UC017         # tagged as use case 17 (PDB Management)
@UC017-F001    # tagged as feature 1 within use case 17
Feature: UC017-F001 PDB Management - Annotation Based

    Background:
        Given the PDB Management Operator is deployed in the 'canvas' namespace
        And the operator is running and ready

    Scenario Outline: Create PDB from deployment annotations with different availability classes
        Given a deployment '<DeploymentName>' with '<Replicas>' replicas in namespace '<Namespace>'
        And the deployment has annotation 'oda.tmforum.org/availability-class' set to '<AvailabilityClass>'
        When the PDB operator processes the deployment
        Then a PDB named '<DeploymentName>-pdb' should be created
        And the PDB should have '<ExpectedMinAvailable>' as minAvailable

    Examples:
    | DeploymentName    | Namespace  | Replicas | AvailabilityClass | ExpectedMinAvailable |
    | standard-app      | components | 3        | standard          | 50%                  |
    | high-avail-app    | components | 5        | high-availability | 75%                  |
    | mission-crit-app  | components | 10       | mission-critical  | 90%                  |
    | non-critical-app  | components | 3        | non-critical      | 25%                  |

    Scenario Outline: Component function classification auto-upgrades availability
        Given a deployment '<DeploymentName>' with '<Replicas>' replicas in namespace '<Namespace>'
        And the deployment has annotation 'oda.tmforum.org/availability-class' set to '<AvailabilityClass>'
        And the deployment has annotation 'oda.tmforum.org/component-function' set to '<ComponentFunction>'
        When the PDB operator processes the deployment
        Then a PDB named '<DeploymentName>-pdb' should be created
        And the PDB should have '<ExpectedMinAvailable>' as minAvailable
        And the operator should log component function upgrade if applicable

    Examples:
    | DeploymentName | Namespace  | Replicas | AvailabilityClass | ComponentFunction | ExpectedMinAvailable |
    | security-std   | components | 5        | standard          | security          | 75%                  |
    | core-std       | components | 4        | standard          | core              | 75%                  |
    | mgmt-std       | components | 3        | standard          | management        | 50%                  |
    | security-ha    | components | 6        | high-availability | security          | 90%                  |

    Scenario: Update PDB when deployment annotations change
        Given a deployment 'update-test' with '4' replicas in namespace 'components'
        And the deployment has annotation 'oda.tmforum.org/availability-class' set to 'standard'
        When the PDB operator processes the deployment
        Then a PDB named 'update-test-pdb' should be created
        And the PDB should have '50%' as minAvailable
        When I update the annotation 'oda.tmforum.org/availability-class' to 'high-availability'
        And the PDB operator processes the deployment
        Then the PDB named 'update-test-pdb' should be updated
        And the PDB should have '75%' as minAvailable

    Scenario: Remove PDB when deployment is deleted
        Given a deployment 'delete-test' with '3' replicas in namespace 'components'
        And the deployment has annotation 'oda.tmforum.org/availability-class' set to 'high-availability'
        When the PDB operator processes the deployment
        Then a PDB named 'delete-test-pdb' should be created
        When I delete the deployment 'delete-test'
        And the PDB operator processes the deletion
        Then the PDB named 'delete-test-pdb' should not exist

    Scenario: Handle invalid availability class gracefully
        Given a deployment 'invalid-test' with '3' replicas in namespace 'components'
        And the deployment has annotation 'oda.tmforum.org/availability-class' set to 'invalid-class'
        When the PDB operator processes the deployment
        Then a PDB should not be created for 'invalid-test'
        And the operator should log a warning about invalid availability class

    Scenario: Skip PDB creation for single replica deployments
        Given a deployment 'single-replica' with '1' replicas in namespace 'components'
        And the deployment has annotation 'oda.tmforum.org/availability-class' set to 'high-availability'
        When the PDB operator processes the deployment
        Then a PDB should not be created for 'single-replica'
        And the operator should log that PDB is skipped for single replica

    Scenario: Handle maintenance window annotations
        Given a deployment 'maintenance-app' with '5' replicas in namespace 'components'
        And the deployment has annotation 'oda.tmforum.org/availability-class' set to 'high-availability'
        And the deployment has annotation 'oda.tmforum.org/maintenance-window' set to '02:00-04:00 UTC'
        When the PDB operator processes the deployment
        Then a PDB named 'maintenance-app-pdb' should be created
        And the PDB should have '75%' as minAvailable
        And the PDB should have maintenance window configuration

    Scenario: Component name tracking for ODA components
        Given a deployment 'oda-component' with '3' replicas in namespace 'components'
        And the deployment has annotation 'oda.tmforum.org/componentName' set to 'product-catalog'
        And the deployment has annotation 'oda.tmforum.org/availability-class' set to 'standard'
        When the PDB operator processes the deployment
        Then a PDB named 'oda-component-pdb' should be created
        And the PDB should have label 'oda.tmforum.org/component-name' set to 'product-catalog'