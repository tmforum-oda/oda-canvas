# The 'business stakeholders' for the canvas Behaviour Driven Design are the Engineering teams
# from the Vendor of a component, from a Systems Integrator who may be integrating and deploying
# a component, or a Service Provider's Operations team who may be supporting a component.

@UC007         # tagged as use case 7
@UC007-F001    # tagged as use feature 1 within use case 7
Feature: UC007-F001 Dependent APIs: Create Dependent API Resource

    Scenario Outline: Create DependentAPI Resource for Component
        Given an example package '<PackageName>' with '<ApiCount>' DependentAPI in its '<SegmentName>' segment
        When I install the '<PackageName>' package as release 'poc'
        Then I should see the '<ResourceName>' DependentAPI resource on the '<ComponentName>' component

    Examples:
       | Name                 | PackageName                                            | ResourceName                  | ComponentName                        | SegmentName        | ApiCount |
       | Core API (catalog)   | productordercaptureandvalidation-v1                    | downstreamproductcatalog      | poc-productordercaptureandvalidation | coreFunction       | 2        |
       | Core API (inventory) | productordercaptureandvalidation-v1                    | downstreamproductinventory    | poc-productordercaptureandvalidation | coreFunction       | 2        |
       | Management API       | productordercaptureandvalidation-mgmt-dependent-API-v1 | downstreamresourcecatalog     | poc-productordercaptureandvalidation | managementFunction | 1        |
       | Security API         | productordercaptureandvalidation-sec-dependent-API-v1  | downstreamuserrolepermissions | poc-productordercaptureandvalidation | securityFunction   | 1        |


    Scenario Outline: Remove DependentAPI Resource when Component deleted
        Given an example package '<PackageName>' with '<ApiCount>' DependentAPI in its '<SegmentName>' segment
        When the release 'poc' is uninstalled
        Then I should not see the '<ResourceName>' DependentAPI resource on the '<ComponentName>' component

    Examples:
       | Name                 | PackageName                                            | ResourceName                  | ComponentName                        | SegmentName        | ApiCount |
       | Core API (catalog)   | productordercaptureandvalidation-v1                    | downstreamproductcatalog      | poc-productordercaptureandvalidation | coreFunction       | 2        |
       | Core API (inventory) | productordercaptureandvalidation-v1                    | downstreamproductinventory    | poc-productordercaptureandvalidation | coreFunction       | 2        |
       | Management API       | productordercaptureandvalidation-mgmt-dependent-API-v1 | downstreamresourcecatalog     | poc-productordercaptureandvalidation | managementFunction | 1        |
       | Security API         | productordercaptureandvalidation-sec-dependent-API-v1  | downstreamuserrolepermissions | poc-productordercaptureandvalidation | securityFunction   | 1        |
