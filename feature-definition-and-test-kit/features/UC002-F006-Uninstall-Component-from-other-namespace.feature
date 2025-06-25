# The 'business stakeholders' for the canvas Behaviour Driven Design are the Engineering teams
# from the Vendor of a component, from a Systems Integrator who may be integrating and deploying 
# a component, or a Service Provider's Operations team who may be supporting a component.

@UC002         # tagged as use case 2
@UC002-F006    # tagged as feature 6 within use case 2
@SkipTest
Feature: UC002-F006 Uninstall a component from non default namespace and verify resources removal

    Scenario Outline: Uninstall a component from non default namespace and verify resources removal
        Given I install the '<PackageName>' package as release '<ReleaseName>' into namespace '<Namespace>'
        And the '<ComponentName>' component has a deployment status of 'Complete'
        When I uninstall the '<PackageName>' package as release '<ReleaseName>' from namespace '<Namespace>'
        And the canvas operator process the uninstallation of components and exposedapis
        Then I should not see the '<ComponentName>' component after '<ReleaseName>' release uninstall from namespace '<Namespace>'

    Examples:
    | PackageName       | ReleaseName | Namespace   | ExposedAPIName           | ComponentName            |
    | productcatalog-v1 |  pcother    | odacompns-1 | productcatalogmanagement | productcatalogmanagement |
