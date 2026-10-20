# The 'business stakeholders' for the canvas Behaviour Driven Design are the Engineering teams
# from the Vendor of a component, from a Systems Integrator who may be integrating and deploying 
# a component, or a Service Provider's Operations team who may be supporting a component.

@UC002         # tagged as use case 2
@UC002-F001    # tagged as use feature 1 within use case 2
Feature: UC002-F001 Install Component

    Scenario Outline: Create ExposedAPI resources for each segment
        Given an example package '<PackageName>' with '<ExposedApiCount>' ExposedAPI in its '<SegmentName>' segment
        When I install the '<PackageName>' package as release '<ReleaseName>'
        And the '<ComponentName>' component has a deployment status of 'Complete'
        Then I should see the '<ExposedAPIName>' ExposedAPI resource on the '<ComponentName>' component

    Examples:
    | Name           | PackageName       | ReleaseName  | ExposedAPIName           | ComponentName                | SegmentName        | ExposedApiCount |
    | Core API       | productcatalog-v1 |      ctk     | productcatalogmanagement | ctk-productcatalogmanagement | coreFunction       | 1               |
    | Management API | productcatalog-v1 |      ctk     | metrics                  | ctk-productcatalogmanagement | managementFunction | 1               |
    | Security API   | productcatalog-v1 |      ctk     | userrolesandpermissions  | ctk-productcatalogmanagement | securityFunction   | 1               |

    Scenario Outline: Create DependentAPI resources for each segment
        Given an example package '<PackageName>' with '<DependentApiCount>' DependentAPI in its '<SegmentName>' segment
        When I install the '<PackageName>' package as release '<ReleaseName>'
        And the '<ComponentName>' component has a deployment status of 'Complete' or 'In-Progress-DepApi'
        Then wait for '5' seconds
        Then I should see the '<DependentAPIName>' DependentAPI resource on the '<ComponentName>' component

    Examples:
    | Name                   | PackageName                                            | ReleaseName | DependentAPIName              | ComponentName                        | SegmentName        | DependentApiCount |
    | Core API (catalog)     | productordercaptureandvalidation-v1                    |      poc    | downstreamproductcatalog      | poc-productordercaptureandvalidation | coreFunction       | 2                 |
    | Core API (inventory)   | productordercaptureandvalidation-v1                    |      poc    | downstreamproductinventory    | poc-productordercaptureandvalidation | coreFunction       | 2                 |
    | Management API         | productordercaptureandvalidation-mgmt-dependent-API-v1 |      poc    | downstreamresourcecatalog     | poc-productordercaptureandvalidation | managementFunction | 1                 |
    | Security API           | productordercaptureandvalidation-sec-dependent-API-v1  |      poc    | downstreamuserrolepermissions | poc-productordercaptureandvalidation | securityFunction   | 1                 |
