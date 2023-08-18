Feature: UC002-F003 Expose APIs: Upgrade component with additional API
    Background:
        Given An example package 'productcatalog-v1beta2' with a 'productcatalog' component with '1' API in its 'coreFunction' segment
        When I install the 'productcatalog-v1beta2' package
        And the 'productcatalog' component has a deployment status of 'Complete'
     
    Scenario: Upgrade component with additional API in coreFunction
        Given An example package 'productcatalog-enhanced-v1beta2' with a 'productcatalog' component with '2' API in its 'coreFunction' segment
        When I upgrade the 'productcatalog-enhanced-v1beta2' package
        Then I should see the 'promotionmanagement' API resource