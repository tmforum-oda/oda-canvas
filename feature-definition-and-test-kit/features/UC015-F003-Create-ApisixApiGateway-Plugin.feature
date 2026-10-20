@UC015
@UC015-F003
@ApisixGateway
Feature: UC015-F003 Create API Resource and Verify Rate-Limiting and Authentication ApisixPlugin Creation for API

    Scenario Outline: Create and Verify ApisixPlugin for ExposedAPI Resource
        Given an example package '<PackageName>' with a '<ComponentName>' component in its '<SegmentName>' segment
        When I install the '<PackageName>' package for testing API resources
        And the Apisix operator processes the deployment
        Then I should see the '<ResourceName>' ExposedAPI resource on the '<ComponentName>' component
        And I should see an ApisixPluginConfig with the '<RateLimitPluginName>' plugin for the '<ResourceName>' ExposedAPI on the '<ComponentName>' component
        And I should see an ApisixPluginConfig with the '<ApiAuthPluginName>' plugin for the '<ResourceName>' ExposedAPI on the '<ComponentName>' component

    Examples:
       | Name           | PackageName                   | ResourceName             | ComponentName                | SegmentName        | RateLimitPluginName | ApiAuthPluginName  |
       | Core API       | productcatalog-v1beta3-plugin | productcatalogmanagement | ctk-productcatalogmanagement | coreFunction       | limit-req           | key-auth           |


    Scenario Outline: Delete API Resource and Verify ApisixPlugin Removal
        Given an existing API resource '<ResourceName>' on component '<ComponentName>' from package '<PackageName>'
        When I delete the '<PackageName>' package
        And the Apisix operator processes the deletion
        Then I should not see the '<ResourceName>' ExposedAPI resource on the '<ComponentName>' component
        And I should not see an ApisixPluginConfig for the '<ResourceName>' ExposedAPI on the '<ComponentName>' component

    Examples:
       | Name           | PackageName                   | ResourceName             | ComponentName                |
       | Core API       | productcatalog-v1beta3-plugin | productcatalogmanagement | ctk-productcatalogmanagement |
