# The 'business stakeholders' for the canvas Behaviour Driven Design are the Engineering teams
# from the Vendor of a component, from a Systems Integrator who may be integrating and deploying 
# a component, or a Service Provider's Operations team who may be supporting a component.

@UC007         # tagged as use case 7
@UC007-F002    # tagged as use feature 2 within use case 7
Feature: UC007-F002 Dependent APIs: Configure Dependent API to single downstream product catalog

    Scenario Outline: Configure DependentAPI for single downstream productcatalog component
        # Install a downstream retail productcatalog component as release r-cat
        Given I install the 'productcatalog-v1' package as release 'r-cat'
        And the 'productcatalogmanagement' component has a deployment status of 'Complete'
        And I should see the 'productcatalogmanagement' ExposedAPI resource on the 'productcatalogmanagement' component with a url on the Service Mesh or Gateway
        # Install the federated productcatalog component that has a dependency on a downstream  productcatalog as release f-cat
        When I install the 'productcatalog-dependendent-API-v1' package as release 'f-cat'
        Then I should see the 'downstreamproductcatalog' DependentAPI resource on the 'productcatalogmanagement' component with a ready status
        And the 'productcatalogmanagement' component has a deployment status of 'Complete'

    Scenario Outline: Populate and verify data in federated product catalog
        # Populate the retail product catalog with sample data
        Given the 'productcatalogmanagement' component in the 'r-cat' release has the following 'category' data:
            | name                      | description                                       |
            | Internet line of product  | Fiber and ADSL broadband products                 |
            | Mobile line of product    | Mobile phones and packages                        |
            | IoT line of product       | IoT devices and solutions                         |
        # Verify that the federated product catalog exposes the populated catalogs
        When I query the 'productcatalogmanagement' component in the 'f-cat' release for 'category' data:
        Then I should see the following 'category' data in the federated product catalog:
            | name                      | description                                       |
            | Internet line of product  | Fiber and ADSL broadband products                 |
            | Mobile line of product    | Mobile phones and packages                        |
            | IoT line of product       | IoT devices and solutions                         |            
