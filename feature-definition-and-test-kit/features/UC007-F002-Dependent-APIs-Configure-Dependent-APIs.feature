# The 'business stakeholders' for the canvas Behaviour Driven Design are the Engineering teams
# from the Vendor of a component, from a Systems Integrator who may be integrating and deploying 
# a component, or a Service Provider's Operations team who may be supporting a component.

@UC007         # tagged as use case 7
@UC007-F002    # tagged as use feature 1 within use case 7
Feature: UC007-F002 Dependent APIs: Configure Dependent API Resource to downstream product catalog

    Scenario Outline: Configure DependentAPI resources for downstream productcatalog component
        # Install a downstream retail productcatalog component as release r-cat
        Given an example package 'productcatalog-v1beta4' with a 'productcatalogmanagement' component with '1' ExposedAPI in its 'coreFunction' segment
        And I install the 'productcatalog-v1beta4' package as release 'r-cat'
        And I should see the 'productcatalogmanagement' ExposedAPI resource on the 'productcatalogmanagement' component with a url on the Service Mesh or Gateway
        # Install the federated productcatalog component that has a dependency on a downstream  productcatalog as release f-cat
        When I install the 'productcatalog-dependendent-API-v1beta4' package as release 'f-cat'
        Then I should see the 'downstreamproductcatalog' DependentAPI resource on the 'productcatalogmanagement' component with a ready status
        And the 'productcatalogmanagement' component has a deployment status of 'Complete'


    Scenario Outline: Configure DependentAPI resources for downstream productcatalog component that becomes available after initial deployment
        Given the release 'f-cat' is not installed
        And the release 'r-cat' is not installed
        # Install the federated productcatalog component that has a dependency on a downstream productcatalog as release f-cat
        When I install the 'productcatalog-dependendent-API-v1beta4' package as release 'f-cat'
        And the 'productcatalogmanagement' component has a deployment status of 'In-Progress-DepApi'

        # Install a downstream retail productcatalog component as release r-cat
        Given an example package 'productcatalog-v1beta4' with a 'productcatalogmanagement' component with '1' ExposedAPI in its 'coreFunction' segment
        And I install the 'productcatalog-v1beta4' package as release 'r-cat'
        And I should see the 'productcatalogmanagement' ExposedAPI resource on the 'productcatalogmanagement' component with a url on the Service Mesh or Gateway

        Then I should see the 'downstreamproductcatalog' DependentAPI resource on the 'productcatalogmanagement' component with a ready status

    