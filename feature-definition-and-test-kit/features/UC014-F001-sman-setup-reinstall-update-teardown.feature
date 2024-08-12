@UC014
@UC014-F001
Feature: Secrets Management - setup, reinstall, update, and teardown

    # tear down?

    Scenario: Create component and check if role and policy are created in vault
        Given a baseline 'productcatalog-v1beta3-sman' package installed as release 'alice'
        When the 'productcatalogmanagement' component for release 'alice' has the deployment status of 'Complete'
        Then in the vault a role for 'alice-productcatalogmanagement' does exist
        And in the vault a policy for 'alice-productcatalogmanagement' does exists
        And in the vault a secret store for 'alice-productcatalogmanagement' does exist

    # Scenario: Uninstall and reinstall compoment will clear assigned secrets
    #     Given a baseline 'productcatalog-v1beta3-sman' package installed as release 'alice'
    #     And the secret 'foo' with value 'bar' does exist
    #     When the 'alice-productcatalog' component is uninstalled
    #     And the package 'productcatalog-v1beta3-sman' with release name 'alice' has been installed again
    #     Then the secret 'foo' with value 'bar' does not exist
 
    # Scenario: Updateing a component will keep secrets
    #     Given a baseline 'productcatalog-v1beta3-sman' package installed as release 'alice'
    #     And the secret 'foo' with value 'bar' does exist
    #     # we need to trigger an side car restart, e.g. changing a env var
    #     When the 'alice-productcatalog' component is updated 
    #     Then the secret 'foo' with value 'bar' does exist

    # Scenario: Uninstall component and check if role and policy are removed
    #     Given a baseline 'productcatalog-v1beta3-sman' package installed as release 'alice'
    #     And the 'alice-productcatalog' component instance has a deployment status of 'Complete'
    #     When the package with release name 'alice' is uninstalled
    #     And the 'alice-productcatalog' component instance does not exist anymore
    #     Then in the vault a role for 'alice-productcatalog' does not exist
    #     And in the vault a policy for 'alice-productcatalog' does not exist
    #     And in the vault a secret store for 'alice-productcatalog' does not exist
