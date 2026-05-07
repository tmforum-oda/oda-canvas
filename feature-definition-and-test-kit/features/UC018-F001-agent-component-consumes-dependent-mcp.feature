# The 'business stakeholders' for the canvas Behaviour Driven Design are the Engineering teams
# from the Vendor of a component, from a Systems Integrator who may be integrating and deploying
# a component, or a Service Provider's Operations team who may be supporting a component.

@UC018
@UC018-F001
Feature: UC018-F001 Agent Component: Expose Agent API and Consume Dependent MCP

    Scenario Outline: Product Agent returns expected grounded outcome for supported query
        Given I install the 'productcatalog-v2' package as release 'pc-2'
        And the 'pc-2-productcatalogmanagement' component has a deployment status of 'Complete'
        And I should see the 'productcatalogmcp' ExposedAPI resource on the 'pc-2-productcatalogmanagement' component with a url on the Service Mesh or Gateway
        And the 'pc-2-productcatalogmanagement' component has the following 'productOffering' data:
            | name                        | description                                              |
            | Basic Firewall for Business | This product offering suggests a firewall service...     |
        When I install the 'productagent-v1' package as release 'pa-1'
        And the 'pa-1-productagent' component has a deployment status of 'Complete'
        And I should see the 'agentquery' ExposedAPI resource on the 'pa-1-productagent' component with a url on the Service Mesh or Gateway
        And I should see the 'agentquery' ExposedAPI resource on the 'pa-1-productagent' component with an implementation ready status on the Service Mesh or Gateway
        And I should see the 'productcatalogmcp' DependentAPI resource on the 'pa-1-productagent' component with a ready status
        When I query the 'pa-1-productagent' component with input 'what product offerings are available in the catalog'
        Then the response status from the 'pa-1-productagent' component should be 'completed'
        And the response from the 'pa-1-productagent' component should contain 'Basic Firewall for Business'
        And the response from the 'pa-1-productagent' component should be grounded in tool results