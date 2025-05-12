# The 'business stakeholders' for the canvas Behaviour Driven Design are the Engineering teams
# from the Vendor of a component, from a Systems Integrator who may be integrating and deploying 
# a component, or a Service Provider's Operations team who may be supporting a component.

@UC002         # tagged as use case 2
@UC002-F005    # tagged as use feature 5 within use case 2
Feature: UC002-F005 Install Component into other namespace

    Scenario Outline: Install a component into a new namespace and verify ExposedAPI resources creation
    		Given I install the '<PackageName>' package as release '<ReleaseName>' into namespace '<Namespace>'
        And the '<ComponentName>' component has a deployment status of 'Complete'
        Then I should see the '<ExposedAPIName>' ExposedAPI resource on the '<ComponentName>' component

    Examples:
    | PackageName       | ReleaseName | Namespace   | ExposedAPIName           | ComponentName            |
    | productcatalog-v1 |  pcother    | odacompns-1 | productcatalogmanagement | productcatalogmanagement |
    | productcatalog-v1 |  pcother    | odacompns-1 | metrics                  | productcatalogmanagement |
    | productcatalog-v1 |  pcother    | odacompns-1 | partyrole                | productcatalogmanagement |

