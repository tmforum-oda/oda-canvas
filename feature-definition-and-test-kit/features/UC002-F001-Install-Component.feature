# The 'business stakeholders' for the canvas Behaviour Driven Design are the Engineering teams
# from the Vendor of a component, from a Systems Integrator who may be integrating and deploying 
# a component, or a Service Provider's Operations team who may be supporting a component.

@UC002         # tagged as use case 2
@UC002-F001    # tagged as use feature 1 within use case 2
Feature: UC002-F001 Install Component

    Scenario Outline: Create ExposedAPI resources for each segment
        Given An example package '<PackageName>' with a '<ComponentName>' component with '<ExposedApiCount>' API in its '<SegmentName>' segment
        When I install the '<PackageName>' package as release '<ReleaseName>'
        Then I should see the '<ExposedAPIName>' ExposedAPI resource on the '<ComponentName>' component

    Examples:
    | Name           | PackageName            | ReleaseName | ExposedAPIName           | ComponentName            | SegmentName        | ExposedApiCount |
    | Core API       | productcatalog-v1beta3 |      pc     | productcatalogmanagement | productcatalogmanagement | coreFunction       | 1               |
    | Management API | productcatalog-v1beta3 |      pc     | metrics                  | productcatalogmanagement | managementFunction | 1               |
    | Security API   | productcatalog-v1beta3 |      pc     | partyrole                | productcatalogmanagement | securityFunction   | 1               |

    Scenario Outline: Create DependentAPI resources for each segment
        Given An example package '<PackageName>' with a '<ComponentName>' component with '<DependentApiCount>' API in its '<SegmentName>' segment
        When I install the '<PackageName>' package as release '<ReleaseName>'
        Then I should see the '<ResourceName>' DependentAPI resource on the '<ComponentName>' component

    Examples:
       | Name           | PackageName              | ReleaseName | DependentAPIName         | ComponentName              | SegmentName        | DependentApiCount |
       | Core API       | productinventory-v1beta3 |      pi     | productcatalogmanagement | productinventorymanagement | coreFunction       | 1                 |
