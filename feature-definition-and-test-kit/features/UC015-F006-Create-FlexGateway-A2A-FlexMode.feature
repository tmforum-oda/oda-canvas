# The 'business stakeholders' for the canvas Behaviour Driven Design are the Engineering teams
# from the Vendor of a component, from a Systems Integrator who may be integrating and deploying
# a component, or a Service Provider's Operations team who may be supporting a component.
#
# UC015-F006 covers the FlexGateway operator handling a2a ExposedAPIs that carry a
# gatewayConfiguration.template.  When Anypoint credentials are present the operator:
#
#   1. Resolves the upstream URL via the Istio ingress host.
#   2. Fetches the A2A agent card from <upstream>/.well-known/agent-card.json
#      (served by the mock nginx included in the productcatalog-a2a-flex-v1 chart).
#   3. Publishes the asset to Anypoint Exchange.
#   4. Creates an API Manager instance and deploys it to the Managed Flex Gateway.
#   5. Applies the policy template (jwt-validation, tracing, a-two-a-agent-card, …).
#   6. Writes status.flexGatewayBind (apiInstanceId, apiPublicUrl) and sets
#      status.implementation.ready = true.
#
# The @FlexGatewayFlex tag causes the Before hook to verify that the flexgateway-operator
# is running AND that valid Anypoint credentials are configured (by reading the
# flexgateway-anypoint-creds Secret).  Scenarios are skipped when either condition is
# not met, making the suite safe to run in Istio-only environments.
#
# Prerequisites (must be true before running this feature):
#   • flexgateway-operator deployed with non-empty ANYPOINT_CLIENT_ID / SECRET / ORG_ID.
#   • A Managed Flex Gateway named in FLEX_GW_NAME is pre-provisioned in Anypoint.
#   • Istio ingress reachable; the mock nginx's agent card endpoint accessible through it.

@UC015
@UC015-F006
@FlexGateway
@FlexGatewayFlex
Feature: UC015-F006 Expose A2A APIs: FlexGateway operator publishes to Anypoint and deploys to Managed Flex Gateway

    Scenario Outline: Install a2a component with template and verify Flex Gateway API instance is created
        Given an example package '<PackageName>' with '<ApiCount>' ExposedAPI in its '<SegmentName>' segment
        When I install the '<PackageName>' package for Flex Gateway testing
        And the FlexGateway operator processes the a2a Flex deployment
        Then I should see the '<ApiName>' ExposedAPI resource on the '<ComponentName>' component
        And the '<ApiName>' ExposedAPI on '<ComponentName>' should have a Flex Gateway API instance bound
        And the '<ApiName>' ExposedAPI on '<ComponentName>' should have a Flex Gateway public URL in its status
        And the '<ApiName>' ExposedAPI on '<ComponentName>' should have implementation ready status

    Examples:
        | Name          | PackageName                  | ApiName  | ComponentName             | SegmentName  | ApiCount |
        | A2A Flex Core | productcatalog-a2a-flex-v1   | agenta2a | ctk-productagenta2aflex   | coreFunction | 1        |


    Scenario Outline: Delete a2a component with template and verify Anypoint API instance is removed
        Given an existing a2a Flex API resource '<ApiName>' on component '<ComponentName>' from package '<PackageName>'
        When I delete the '<PackageName>' Flex package
        And the FlexGateway operator processes the Flex deletion
        Then I should not see the '<ApiName>' ExposedAPI resources on the '<ComponentName>' component
        And the Anypoint API instance for '<ApiName>' on '<ComponentName>' should be removed from Flex Gateway status

    Examples:
        | Name          | PackageName                  | ApiName  | ComponentName             | SegmentName  | ApiCount |
        | A2A Flex Core | productcatalog-a2a-flex-v1   | agenta2a | ctk-productagenta2aflex   | coreFunction | 1        |
