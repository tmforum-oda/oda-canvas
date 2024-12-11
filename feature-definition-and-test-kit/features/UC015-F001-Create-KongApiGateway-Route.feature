@UC015
@UC015-F001
@KongGateway
Feature: UC015-F001 Expose APIs: Create and Verify HTTProute for ExposedAPI Resource

    Scenario Outline: Create API Resource and Verify HTTPRoute Creation for API
        Given an example package '<PackageName>' with a '<ComponentName>' component with '<ApiCount>' ExposedAPI in its '<SegmentName>' segment
        When I install the '<PackageName>' package
        And the Kong operator processes the deployment
        Then I should see the '<ResourceName>' ExposedAPI resource on the '<ComponentName>' component
        And I should see an HTTPRoute resource created for "<ComponentName>"

    Examples:
       | Name           | PackageName            | ResourceName             | ComponentName            | SegmentName        | ApiCount |
       | Core API       | productcatalog-v1beta3 | productcatalogmanagement | productcatalogmanagement | coreFunction       | 1        |


    Scenario Outline: Delete API Resource and Verify HTTPRoute Removal
        Given an existing API resource '<ResourceName>' on component '<ComponentName>' from package '<PackageName>'
        When I delete the '<PackageName>' package
        And the Kong operator processes the deletion
        Then I should not see the '<ResourceName>' ExposedAPI resources on the '<ComponentName>' component
        And I should not see an HTTPRoute resource for "<ComponentName>"

    Examples:
       | Name           | PackageName            | ResourceName             | ComponentName            | SegmentName        | ApiCount |
       | Core API       | productcatalog-v1beta3 | productcatalogmanagement | productcatalogmanagement | coreFunction       | 1        |
    