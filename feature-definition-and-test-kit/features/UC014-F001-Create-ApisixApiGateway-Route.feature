@UC014
@UC014-F001
@ApisixGateway
Feature: UC014-F001 Expose APIs: Create and Verify ApisixRoute for ExposedAPI Resource

    Scenario Outline: Create API Resource and Verify ApisixRoute Creation for API
        Given an example package '<PackageName>' with a '<ComponentName>' component with '<ApiCount>' ExposedAPI in its '<SegmentName>' segment
        When I install the '<PackageName>' package
        And the Apisix operator processes the deployment
        Then I should see the '<ResourceName>' ExposedAPI resource on the '<ComponentName>' component
        And I should see an ApisixRoute resource created for "<ComponentName>"

    Examples:
       | Name           | PackageName            | ResourceName             | ComponentName            | SegmentName        | ApiCount |
       | Core API       | productcatalog-v1beta3 | productcatalogmanagement | productcatalogmanagement | coreFunction       | 1        |


    Scenario Outline: Delete API Resource and Verify ApisixRoute Removal
        Given an existing API resource '<ResourceName>' on component '<ComponentName>' from package '<PackageName>'
        When I delete the '<PackageName>' package
        And the Apisix operator processes the deletion
        Then I should not see the '<ResourceName>' ExposedAPI resources on the '<ComponentName>' component
        And I should not see an ApisixRoute resource for "<ComponentName>"

    Examples:
       | Name           | PackageName            | ResourceName             | ComponentName            | SegmentName        | ApiCount |
       | Core API       | productcatalog-v1beta3 | productcatalogmanagement | productcatalogmanagement | coreFunction       | 1        |
    
