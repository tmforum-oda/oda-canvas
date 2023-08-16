Feature: UC002-F003-Verify API implementation is ready

    Scenario: Verify API Resource is ready for Core API
        Given An example component 'productcatalog' with '1' API in its 'coreFunction' segment
        When I install the 'productcatalog' component
        Then I should see the 'productcatalogmanagement' API resource with an implementation ready status on the Service Mesh or Gateway

    Scenario: Verify API Resource is ready for Management API
        Given An example component 'productcatalog' with '1' API in its 'managementFunction' segment
        When I install the 'productcatalog' component
        Then I should see the 'metrics' API resource with an implementation ready status on the Service Mesh or Gateway

    Scenario: Verify API Resource is ready for Security API
        Given An example component 'productcatalog' with '1' API in its 'securityFunction' segment
        When I install the 'productcatalog' component
        Then I should see the 'partyrole' API resource with an implementation ready status on the Service Mesh or Gateway


