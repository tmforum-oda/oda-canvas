# The 'business stakeholders' for the canvas Behaviour Driven Design are the Engineering teams
# from the Vendor of a component, from a Systems Integrator who may be integrating and deploying 
# a component, or a Service Provider's Operations team who may be supporting a component.

@UC002         # tagged as use case 2
@UC002-F004    # tagged as feature 4 within use case 2
Feature: UC002-F004 Uninstall a component and verify resources removal

    Scenario Outline: Uninstall a component and verify resources removal
        Given I install the '<PackageName>' package as release '<ReleaseName>' from the '<RepoName>' repository
        And the '<ComponentName>' component has a deployment status of 'Complete' for the '<ReleaseName>' release
        When I uninstall the '<PackageName>' package as release '<ReleaseName>'
        And the canvas operator process the uninstallation of components and exposedapis
        Then I should not see the '<ComponentName>' component after '<ReleaseName>' release uninstall

    Examples:
    | RepoName       | ReferenceExampleRepoURL                                         | PackageName       | ReleaseName  |  ComponentName            |
    | oda-components | https://tmforum-oda.github.io/reference-example-components      | productcatalog    | pc-repo      |  productcatalogmanagement |