# The 'business stakeholders' for the canvas Behaviour Driven Design are the Engineering teams
# from the Vendor of a component, from a Systems Integrator who may be integrating and deploying
# a component, or a Service Provider's Operations team who may be supporting a component.
#
# UC015-F005 covers the FlexGateway operator handling a2a ExposedAPIs that carry NO
# gatewayConfiguration.template.  In this case the operator creates an Istio VirtualService
# regardless of whether Anypoint credentials are present, making it the correct path for:
#
#   • ISTIO_ONLY_MODE  — operator started without Anypoint credentials.
#   • Flex mode fallback — credentials present but component author chose not to supply a
#                          template (Istio routing is sufficient for the a2a traffic).
#
# The @FlexGateway tag causes the Before hook in FlexGatewayManagementSteps.js to verify
# that the flexgateway-operator Deployment is running before executing each scenario.
# Scenarios are skipped automatically when the operator is absent.

@UC015
@UC015-F005
@FlexGateway
Feature: UC015-F005 Expose A2A APIs: FlexGateway operator creates Istio VirtualService for a2a ExposedAPI (no template)

    Scenario Outline: Install a2a component and verify Istio VirtualService is created
        Given an example package '<PackageName>' with '<ApiCount>' ExposedAPI in its '<SegmentName>' segment
        When I install the '<PackageName>' package
        And the FlexGateway operator processes the a2a Istio deployment
        Then I should see the '<ApiName>' ExposedAPI resource on the '<ComponentName>' component
        And I should see a VirtualService created for '<ApiName>' on the '<ComponentName>' component
        And the '<ApiName>' ExposedAPI on '<ComponentName>' should have implementation ready status
        And the '<ApiName>' ExposedAPI on '<ComponentName>' should have a public URL in its status

    Examples:
        | Name     | PackageName             | ApiName  | ComponentName          | SegmentName  | ApiCount |
        | A2A Core | productcatalog-a2a-v1   | agenta2a | ctk-productagenta2a    | coreFunction | 1        |


    Scenario Outline: Delete a2a component and verify Istio VirtualService is removed
        Given an existing a2a API resource '<ApiName>' on component '<ComponentName>' from package '<PackageName>'
        When I delete the '<PackageName>' package
        And the FlexGateway operator processes the a2a deletion
        Then I should not see the '<ApiName>' ExposedAPI resources on the '<ComponentName>' component
        And I should not see a VirtualService for '<ApiName>' on the '<ComponentName>' component

    Examples:
        | Name     | PackageName             | ApiName  | ComponentName          | SegmentName  | ApiCount |
        | A2A Core | productcatalog-a2a-v1   | agenta2a | ctk-productagenta2a    | coreFunction | 1        |
