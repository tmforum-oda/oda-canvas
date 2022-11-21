Feature: IGXXX-UCXXX-F001-Generate API Resource

    Scenario: Generate API Resource for Core API
        Given An example component helm chart 'productcatalog' with at least one API in its 'coreFunction' segment
        When I install the 'productcatalog' component helm chart
        Then I should see the 'productcatalogmanagement' API resource in the Kubernetes cluster

    Scenario: Generate API Resource for Management API
        Given An example component helm chart 'productcatalog' with at least one API in its 'management' segment
        When I install the 'productcatalog' component helm chart
        Then I should see the 'metrics' API resource in the Kubernetes cluster

    Scenario: Generate API Resource for Security API
        Given An example component helm chart 'productcatalog' with at least one API in its 'security' segment
        When I install the 'productcatalog' component helm chart
        Then I should see the 'partyrole' API resource in the Kubernetes cluster



