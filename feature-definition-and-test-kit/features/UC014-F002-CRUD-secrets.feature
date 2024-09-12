@UC014 @UC014-F002 @SECRET-MANAGEMENT
Feature: Secrets Management - CRUD secrets

    Background: Canvas with fresh productcatalog-v1beta3-sman catalog
        Given the 'alice' release is not installed
        And a baseline 'productcatalog-v1beta3-sman' package installed as release 'alice'

    Scenario: Creates secret
        When the 'alice-vault-inspector' component creates the secret 'foo' with value 'bar' 
        Then the 'alice-vault-inspector' component can read the secret 'foo' and its value is 'bar'

    Scenario: Modify secret
        Given the 'alice-vault-inspector' component has the secret 'foo' with value 'bar'
        When the 'alice-vault-inspector' component updates the secret 'foo' to value 'baz'
        Then the 'alice-vault-inspector' component can read the secret 'foo' and its value is 'baz'

    Scenario: Delete secret
        Given the 'alice-vault-inspector' component has the secret 'foo' with value 'bar'
        When the 'alice-vault-inspector' component deletes the secret 'foo'
        Then the 'alice-vault-inspector' component can not read the secret 'foo'
