# The 'business stakeholders' for the canvas Behaviour Driven Design are the Engineering teams
# from the Vendor of a component, from a Systems Integrator who may be integrating and deploying 
# a component, or a Service Provider's Operations team who may be supporting a component.

@UC017         # tagged as use case 17 (PDB Management)
@UC017-F004    # tagged as feature 4 within use case 17
Feature: UC017-F004 PDB Management - Edge Cases and Error Handling

    Background:
        Given the PDB Management Operator is deployed in the 'canvas' namespace
        And the operator is running and ready

    Scenario: Verify PDB remains for multi-replica deployment after scaling
        Given a deployment 'scale-test' with '3' replicas in namespace 'components'
        And the deployment has annotation 'oda.tmforum.org/availability-class' set to 'standard'
        And a PDB 'scale-test-pdb' exists with '50%' minAvailable
        When I scale the deployment 'scale-test' to '2' replicas
        And the PDB operator processes the scaling event
        Then the PDB 'scale-test-pdb' should still exist
        And the PDB should have '50%' as minAvailable

    Scenario: Handle deployment scaling from single to multiple replicas
        Given a deployment 'scale-up-test' with '1' replica in namespace 'components'
        And the deployment has annotation 'oda.tmforum.org/availability-class' set to 'high-availability'
        When I scale the deployment 'scale-up-test' to '5' replicas
        And the PDB operator processes the scaling event
        Then a PDB named 'scale-up-test-pdb' should be created
        And the PDB should have '75%' as minAvailable

    Scenario: Verify PDB creation with different replica counts
        Given a deployment 'replica-test' with '5' replicas in namespace 'components'
        And the deployment has annotation 'oda.tmforum.org/availability-class' set to 'high-availability'
        When the PDB operator processes the deployment
        Then a PDB named 'replica-test-pdb' should be created
        And the PDB should have '75%' as minAvailable

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
        Given a deployment 'max-replicas' with '20' replicas in namespace 'components'
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

