# The 'business stakeholders' for the canvas Behaviour Driven Design are the Engineering teams
# from the Vendor of a component, from a Systems Integrator who may be integrating and deploying 
# a component, or a Service Provider's Operations team who may be supporting a component.

@UC002         # tagged as use case 2
@UC002-F003    # tagged as feature 3 within use case 2
Feature: UC002-F003 Install Component from Repository

    Scenario Outline: Install a component and verify ExposedAPI resources creation
        Given the repository '<RepoName>' with URL '<ReferenceExampleRepoURL>' is added and updated
        When I install the '<PackageName>' package as release '<ReleaseName>' from the '<RepoName>' repository 
        And the '<ComponentName>' component has a deployment status of 'Complete' for the '<ReleaseName>' release
        Then I should see the '<ExposedAPIName>' ExposedAPI resource on the '<ComponentName>' component

    Examples:
    | RepoName       | ReferenceExampleRepoURL                                         | PackageName       | ReleaseName  |  ComponentName            |  ExposedAPIName             |
    | oda-components | https://tmforum-oda.github.io/reference-example-components      | productcatalog    | pc-repo      |  productcatalogmanagement |  productcatalogmanagement   |
    | oda-components | https://tmforum-oda.github.io/reference-example-components      | productcatalog    | pc-repo      |  productcatalogmanagement |  metrics                    |
    | oda-components | https://tmforum-oda.github.io/reference-example-components      | productcatalog    | pc-repo      |  productcatalogmanagement |  partyrole                  |
    | oda-components | https://tmforum-oda.github.io/reference-example-components      | productcatalog    | pc-repo      |  productcatalogmanagement |  promotionmanagement        |

