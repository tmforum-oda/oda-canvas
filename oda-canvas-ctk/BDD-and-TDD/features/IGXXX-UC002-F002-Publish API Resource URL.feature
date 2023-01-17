Feature: IGXXX-UC002-F002-Publish API Resource URL

    Scenario: Test API Resource URL for Core API
        Given An example component 'productcatalog' with '1' API in its 'coreFunction' segment
        When I install the 'productcatalog' component
        Then I should see the 'productcatalogmanagement' API resource with a url on the Service Mesh or Gateway

    Scenario: Test API Resource URL for Management API
        Given An example component 'productcatalog' with '1' API in its 'management' segment
        When I install the 'productcatalog' component
        Then I should see the 'metrics' API resource with a url on the Service Mesh or Gateway

    Scenario: Test API Resource URL for Security API
        Given An example component 'productcatalog' with '1' API in its 'security' segment
        When I install the 'productcatalog' component
        Then I should see the 'partyrole' API resource with a url on the Service Mesh or Gateway



