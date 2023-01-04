Feature: IGXXX-UCXXX-F003-Upgrade component with additional API
    Background:
        Given An example component helm chart 'productcatalog' with '1' API in its 'coreFunction' segment
        And An example component helm chart 'productcatalog' has been installed
        And the 'productcatalog' component has a deployment status of 'Complete'
     
    Scenario: Upgrade component with additional API in coreFunction
        Given An example component helm chart 'productcatalogadd' with '2' API in its 'coreFunction' segment
        When I upgrade the 'productcatalogadd' component helm chart
        Then I should see the 'promotionmanagement' API resource