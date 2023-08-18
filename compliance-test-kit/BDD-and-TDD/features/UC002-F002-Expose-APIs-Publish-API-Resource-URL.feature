Feature: UC002-F002 Expose APIs: Publish API Resource URL

    Scenario: Test API Resource URL for Core API
        Given An example package 'productcatalog-v1beta2' with a 'productcatalog' component with '1' API in its 'coreFunction' segment
        When I install the 'productcatalog-v1beta2' package
        Then I should see the 'productcatalogmanagement' API resource with a url on the Service Mesh or Gateway

    Scenario: Test API Resource URL for Management API
        Given An example package 'productcatalog-v1beta2' with a 'productcatalog' component with '1' API in its 'managementFunction' segment
        When I install the 'productcatalog-v1beta2' package
        Then I should see the 'metrics' API resource with a url on the Service Mesh or Gateway

    Scenario: Test API Resource URL for Security API
        Given An example package 'productcatalog-v1beta2' with a 'productcatalog' component with '1' API in its 'securityFunction' segment
        When I install the 'productcatalog-v1beta2' package
        Then I should see the 'partyrole' API resource with a url on the Service Mesh or Gateway



