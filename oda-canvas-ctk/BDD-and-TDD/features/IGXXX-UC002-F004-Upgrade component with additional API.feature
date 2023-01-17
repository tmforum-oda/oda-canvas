Feature: IGXXX-UCXXX-F003-Upgrade component with additional API
    Background:
        Given An example component 'productcatalog' with '1' API in its 'coreFunction' segment
        And An example component 'productcatalog' has been installed
        And the 'productcatalog' component has a deployment status of 'Complete'
     
    Scenario: Upgrade component with additional API in coreFunction
        Given An example component 'productcatalogadd' with '2' API in its 'coreFunction' segment
        When I upgrade the 'productcatalogadd' component
        Then I should see the 'promotionmanagement' API resource