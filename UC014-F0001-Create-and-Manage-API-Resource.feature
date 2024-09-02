# The 'business stakeholders' for the canvas Behaviour Driven Design are the Engineering teams
# from the Vendor of a component, from a Systems Integrator who may be integrating and deploying 
# a component, or a Service Provider's Operations team who may be supporting a component.


@UC014         # tagged as use case 14
@UC014-F0001    # tagged as use feature 01 within use case 14
Feature: UC014-F0001 : Create API Resource

    Scenario: Create or Update HTTPRoute for an API Resource
        Given an API resource with path '<Path>'
        When the API resource is created or updated
        Then an HTTPRoute should be created or updated in the 'components' namespace
        And the HTTPRoute should be associated with the correct service
        And the HTTPRoute should have the appropriate annotations

    Examples:
       | Path               |
       | /pc-productcatalogmanagement/tmf-api/productCatalogManagement/v4 |
       
     Scenario: Apply Rate Limiting Plugin
        Given an API resource with rate limiting enabled and a limit of <Limit> requests per minute
        When the API resource is created or updated
        Then a rate limiting plugin should be created or updated in the 'components' namespace
        And the plugin should be associated with the correct API resource

     Examples:
       | Limit |
       | 100   |
       | 200   |

     Scenario: Apply API Key Verification Plugin
        Given an API resource with API key verification enabled
        When the API resource is created or updated
        Then an API key verification plugin should be created or updated in the 'components' namespace
        And the plugin should be associated with the correct API resource

     
     Scenario: Manage Plugins from URL Template
         Given an API resource with a URL template for plugins '<URL>'
         When the API resource is created or updated
         Then plugins should be downloaded and applied from the URL template
         And the applied plugins should be associated with the correct API resource

     Examples:
       |          Name              |
       | http://example.com/plugin1 |
       | http://example.com/plugin2 |

     Scenario: Delete API Resource
        Given an API resource with path '<Path>' is deleted
        When the deletion event is triggered
        Then the associated HTTPRoute should be automatically deleted
        And the deletion should be logged

     Examples:
       | Path               |
       | /api/v1/resource1  |
       | /api/v1/resource2  |


  

