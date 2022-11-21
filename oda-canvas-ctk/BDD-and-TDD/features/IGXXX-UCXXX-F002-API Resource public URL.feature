Feature: IGXXX-UCXXX-F002-API Resource public URL

    Scenario: Test API Resource public URL for Core API
        Given An example component helm chart 'productcatalog' with at least one API in its 'coreFunction' segment
        When I install the 'productcatalog' component helm chart
        Then I should see the 'productcatalogmanagement' API resource with a public url in the Kubernetes cluster

    Scenario: Test API Resource public URL for Management API
        Given An example component helm chart 'productcatalog' with at least one API in its 'management' segment
        When I install the 'productcatalog' component helm chart
        Then I should see the 'metrics' API resource with a public url in the Kubernetes cluster

    Scenario: Test API Resource public URL for Security API
        Given An example component helm chart 'productcatalog' with at least one API in its 'security' segment
        When I install the 'productcatalog' component helm chart
        Then I should see the 'partyrole' API resource with a public url in the Kubernetes cluster



