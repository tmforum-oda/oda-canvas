# The 'business stakeholders' for the canvas Behaviour Driven Design are the Engineering teams
# from the Vendor of a component, from a Systems Integrator who may be integrating and deploying
# a component, or a Service Provider's Operations team who may be supporting a component.

@UC007         # tagged as use case 7
@UC007-F002    # tagged as use feature 2 within use case 7
Feature: UC007-F002 Dependent APIs: Configure Dependent APIs to a downstream Product Catalog and Product Inventory

    Scenario: Configure DependentAPIs for a product order component
        # Install the downstream product catalog component as release r-cat
        Given I install the 'productcatalog-depapitest-v1' package as release 'r-cat'
        And the 'r-cat-productcatalogmanagement' component has a deployment status of 'Complete'
        And I should see the 'productcatalogmanagement' ExposedAPI resource on the 'r-cat-productcatalogmanagement' component with a url on the Service Mesh or Gateway
        # Install the downstream product inventory component as release r-inv
        And I install the 'productinventory-v1' package as release 'r-inv'
        And the 'r-inv-productinventory' component has a deployment status of 'Complete'
        And I should see the 'productinventorymanagement' ExposedAPI resource on the 'r-inv-productinventory' component with a url on the Service Mesh or Gateway
        # Install the product order component, which depends on a product catalog and a product inventory, as release poc
        When I install the 'productordercaptureandvalidation-v1' package as release 'poc'
        Then I should see the 'downstreamproductcatalog' DependentAPI resource on the 'poc-productordercaptureandvalidation' component with a ready status
        And I should see the 'downstreamproductinventory' DependentAPI resource on the 'poc-productordercaptureandvalidation' component with a ready status
        And the 'poc-productordercaptureandvalidation' component has a deployment status of 'Complete'

    Scenario: Validate a product order against the downstream catalog and create its product in the downstream inventory
        # Populate the downstream product catalog with a product offering
        Given the 'r-cat-productcatalogmanagement' component has the following 'productOffering' data:
            | name                    | description                    |
            | Fibre 900 Pro Broadband | Fibre broadband up to 900 Mbps |
        # The product order component looks the offering up through its downstreamproductcatalog DependentAPI
        When I create a product order in the 'poc-productordercaptureandvalidation' component for the 'Fibre 900 Pro Broadband' product offering from the 'r-cat-productcatalogmanagement' component
        Then the product order should be created with a state of 'acknowledged'
        # It creates the ordered product through its downstreamproductinventory DependentAPI
        And the 'r-inv-productinventory' component should have the product from the product order

    Scenario: Reject a product order for a product offering that is not in the downstream catalog
        When I create a product order in the 'poc-productordercaptureandvalidation' component for a product offering with id 'not-in-the-catalog'
        Then the product order should be rejected with a status of '422'
