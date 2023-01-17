Feature: IGXXX-UCXXX-F003-Upgrade component with removed API
    Background:
        Given An example component 'productcatalogadd' with '2' API in its 'coreFunction' segment
        And An example component 'productcatalogadd' has been installed
        # And the 'productcatalog' component has a deployment status of 'Complete' - won't work at the moment as there is no API implementation for promotionmanagement
     
    Scenario: Upgrade component with removed API in coreFunction
        Given An example component 'productcatalog' with '1' API in its 'coreFunction' segment
        When I upgrade the 'productcatalog' component
        Then I should not see the 'promotionmanagement' API resource