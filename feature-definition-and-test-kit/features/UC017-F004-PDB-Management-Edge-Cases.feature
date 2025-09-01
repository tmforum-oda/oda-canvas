# The 'business stakeholders' for the canvas Behaviour Driven Design are the Engineering teams
# from the Vendor of a component, from a Systems Integrator who may be integrating and deploying 
# a component, or a Service Provider's Operations team who may be supporting a component.

@UC017         # tagged as use case 17 (PDB Management)
@UC017-F004    # tagged as feature 4 within use case 17
Feature: UC017-F004 PDB Management - Edge Cases and Error Handling

    Background:
        Given the PDB Management Operator is deployed in the 'canvas' namespace
        And the operator is running and ready

    Scenario: Handle deployment scaling to single replica
        Given a deployment 'scale-test' with '3' replicas in namespace 'components'
        And the deployment has annotation 'oda.tmforum.org/availability-class' set to 'standard'
        And a PDB 'scale-test-pdb' exists with '50%' minAvailable
        When I scale the deployment 'scale-test' to '1' replica
        And the PDB operator processes the scaling event
        Then the PDB 'scale-test-pdb' should be deleted
        And the operator should log PDB removal due to single replica

    Scenario: Handle deployment scaling from single to multiple replicas
        Given a deployment 'scale-up-test' with '1' replica in namespace 'components'
        And the deployment has annotation 'oda.tmforum.org/availability-class' set to 'high-availability'
        When I scale the deployment 'scale-up-test' to '5' replicas
        And the PDB operator processes the scaling event
        Then a PDB named 'scale-up-test-pdb' should be created
        And the PDB should have '75%' as minAvailable

    Scenario: Handle conflicting policies with same priority
        Given an AvailabilityPolicy 'policy-a' with priority '100' targeting label 'app=conflict'
        And an AvailabilityPolicy 'policy-b' with priority '100' targeting label 'app=conflict'
        When I create a deployment 'conflict-test' with label 'app=conflict'
        And the PDB operator processes the deployment
        Then a PDB should be created for 'conflict-test'
        And the operator should log policy conflict resolution
        And the policy with alphabetically first name should be applied

    Scenario: Handle rapid annotation changes
        Given a deployment 'rapid-change' with '3' replicas in namespace 'components'
        And the deployment has annotation 'oda.tmforum.org/availability-class' set to 'standard'
        When I rapidly update the availability class annotation 10 times
        And the PDB operator processes all changes
        Then exactly one PDB named 'rapid-change-pdb' should exist
        And the PDB should reflect the final annotation value

    Scenario: Recovery from operator restart
        Given a deployment 'restart-test' with '4' replicas in namespace 'components'
        And the deployment has annotation 'oda.tmforum.org/availability-class' set to 'high-availability'
        And a PDB 'restart-test-pdb' exists with '75%' minAvailable
        When the PDB operator is restarted
        And the operator completes initialization
        Then the PDB 'restart-test-pdb' should remain unchanged
        And the operator should reconcile existing PDBs on startup

    Scenario: Handle namespace deletion
        Given a namespace 'temp-namespace' exists
        And a deployment 'ns-test' exists in namespace 'temp-namespace'
        And the deployment has annotation 'oda.tmforum.org/availability-class' set to 'standard'
        And a PDB 'ns-test-pdb' exists in namespace 'temp-namespace'
        When I delete the namespace 'temp-namespace'
        Then the operator should handle namespace deletion gracefully
        And no orphaned resources should remain

    Scenario: Handle malformed annotations
        Given a deployment 'malformed-test' with '3' replicas in namespace 'components'
        When I set annotation 'oda.tmforum.org/availability-class' to '{{invalid-json}}'
        And the PDB operator processes the deployment
        Then a PDB should not be created for 'malformed-test'
        And the operator should log annotation parsing error

    Scenario: Maximum replicas boundary test
        Given a deployment 'max-replicas' with '1000' replicas in namespace 'components'
        And the deployment has annotation 'oda.tmforum.org/availability-class' set to 'mission-critical'
        When the PDB operator processes the deployment
        Then a PDB named 'max-replicas-pdb' should be created
        And the PDB should have '90%' as minAvailable
        And the operator should handle large replica count correctly

    Scenario: Zero replicas handling
        Given a deployment 'zero-replicas' with '0' replicas in namespace 'components'
        And the deployment has annotation 'oda.tmforum.org/availability-class' set to 'standard'
        When the PDB operator processes the deployment
        Then a PDB should not be created for 'zero-replicas'
        And the operator should skip PDB creation for zero replicas

    Scenario: Handle PDB manual modification
        Given a deployment 'manual-test' with '4' replicas in namespace 'components'
        And the deployment has annotation 'oda.tmforum.org/availability-class' set to 'standard'
        And a PDB 'manual-test-pdb' exists with '50%' minAvailable
        When I manually modify the PDB 'manual-test-pdb' to have '25%' minAvailable
        And the PDB operator reconciles the PDB
        Then the PDB 'manual-test-pdb' should be restored to '50%' minAvailable
        And the operator should log PDB drift correction