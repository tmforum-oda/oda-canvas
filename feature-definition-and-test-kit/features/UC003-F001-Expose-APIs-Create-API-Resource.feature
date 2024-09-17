# The 'business stakeholders' for the canvas Behaviour Driven Design are the Engineering teams
# from the Vendor of a component, from a Systems Integrator who may be integrating and deploying 
# a component, or a Service Provider's Operations team who may be supporting a component.

@UC003         # tagged as use case 3
@UC003-F001    # tagged as use feature 1 within use case 3
Feature: UC003-F001 Expose APIs: Create API Resource

    Scenario Outline: Create API Resource for API
        Given an example package '<PackageName>' with a '<ComponentName>' component with '<ApiCount>' ExposedAPI in its '<SegmentName>' segment
        When I install the '<PackageName>' package
        Then I should see the '<ResourceName>' ExposedAPI resource on the '<ComponentName>' component

    Examples:
       | Name           | PackageName            | ResourceName             | ComponentName            | SegmentName        | ApiCount |
       | Core API       | productcatalog-v1beta3 | productcatalogmanagement | productcatalogmanagement | coreFunction       | 1        |
       | Management API | productcatalog-v1beta3 | metrics                  | productcatalogmanagement | managementFunction | 1        |
       | Security API   | productcatalog-v1beta3 | partyrole                | productcatalogmanagement | securityFunction   | 1        |
