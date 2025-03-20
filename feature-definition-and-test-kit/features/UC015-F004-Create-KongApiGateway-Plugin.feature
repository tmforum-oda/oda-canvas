@UC015
@UC015-F002
@KongGateway
Feature:UC015-F004 Create API Resource and Verify Rate-Limiting and Authentication KongPlugin Creation for API

  Scenario: Create and Verify KongPlugin for ExposedAPI Resource
    Given an example package "productcatalog-v1beta3-plugin" with a '<ComponentName>' component in its "coreFunction" segment
    When I install the "productcatalog-v1beta3-plugin" package for testing API resources
    And the Kong operator processes the deployment
    Then I should see an KongPlugin Rate Limit resource created for '<ComponentName>' with the name '<RateLimitPluginName>'
    Then I should see an KongPlugin API Authentication resource created for '<ComponentName>' with the name '<ApiAuthPluginName>'

    Examples:
       | Name           | PackageName                   | ResourceName             | ComponentName            | SegmentName        | ApiCount | RateLimitPluginName | ApiAuthPluginName  |
       | Core API       | productcatalog-v1beta3-plugin | productcatalogmanagement | productcatalogmanagement | coreFunction       | 1        | rate-limit          | apiauthentication  |


    Scenario Outline: Delete API Resource and Verify KongPlugin Removal
        Given an existing API resource '<ResourceName>' on component '<ComponentName>' from package '<PackageName>'
        When I delete the 'productcatalog-v1beta3-plugin' package
        And the Kong operator processes the deletion
        Then I should not see the '<ResourceName>' ExposedAPI resources on the '<ComponentName>' component
        And I should not see an KongPlugin resource for "<ComponentName>"

    Examples:
       | Name           | PackageName                   | ResourceName             | ComponentName            | SegmentName        | ApiCount |
       | Core API       | productcatalog-v1beta3-plugin | productcatalogmanagement | productcatalogmanagement | coreFunction       | 1        |
