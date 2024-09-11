@UC014
@UC014-F004
Feature: Secrets Management - Bobs secrets are isolated from Alice secrets

    Background:
        Given a baseline 'productcatalog-v1beta3-sman' package installed as release 'alice'
        And the 'alice-vault-inspector' component instance has a deployment status of 'Complete'
        And the package 'vault-inspector' with release name 'bob' has been installed
        And the 'bob-vault-inspector' component instance has a deployment status of 'Complete'

    Scenario: Bob can not read secret created by Alice
    
    Scenario: Alice can not read secret created by Bob





