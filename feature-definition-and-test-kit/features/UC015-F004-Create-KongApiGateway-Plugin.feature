@UC015
@UC015-F004
@KongGateway
Feature: UC015-F004 Create API Resource and Verify Rate-Limiting and Authentication KongPlugin Creation for API

    Scenario Outline: Create and Verify KongPlugin for ExposedAPI Resource
        Given an example package '<PackageName>' with a '<ComponentName>' component in its '<SegmentName>' segment
        When I install the '<PackageName>' package for testing API resources
        And the Kong operator processes the deployment
        Then I should see the '<ResourceName>' ExposedAPI resource on the '<ComponentName>' component
        And I should see a '<RateLimitPluginName>' KongPlugin resource created for the '<ResourceName>' ExposedAPI on the '<ComponentName>' component
        And I should see a '<ApiAuthPluginName>' KongPlugin resource created for the '<ResourceName>' ExposedAPI on the '<ComponentName>' component

    Examples:
       | Name           | PackageName                   | ResourceName             | ComponentName                | SegmentName        | RateLimitPluginName | ApiAuthPluginName  |
       | Core API       | productcatalog-v1beta3-plugin | productcatalogmanagement | ctk-productcatalogmanagement | coreFunction       | rate-limit          | apiauthentication  |


    Scenario Outline: Delete API Resource and Verify KongPlugin Removal
        Given an existing API resource '<ResourceName>' on component '<ComponentName>' from package '<PackageName>'
        When I delete the '<PackageName>' package
        And the Kong operator processes the deletion
        Then I should not see the '<ResourceName>' ExposedAPI resource on the '<ComponentName>' component
        And I should not see a '<RateLimitPluginName>' KongPlugin resource for the '<ResourceName>' ExposedAPI on the '<ComponentName>' component
        And I should not see a '<ApiAuthPluginName>' KongPlugin resource for the '<ResourceName>' ExposedAPI on the '<ComponentName>' component

    Examples:
       | Name           | PackageName                   | ResourceName             | ComponentName                | RateLimitPluginName | ApiAuthPluginName  |
       | Core API       | productcatalog-v1beta3-plugin | productcatalogmanagement | ctk-productcatalogmanagement | rate-limit          | apiauthentication  |
