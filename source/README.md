# ODA Canvas source code

This folder contains the source code for the ODA Canvas. The ODA Canvas provides access to a range of common services (for identity management, authentication, observability etc) and has a set of [Software Operators](operators/README.md) that automatically configure these services based on requirements defined in each ODA Component YAML specification. The operators are packaged as docker images and are deployed as part of the canvas. 

The custom resource definitions (CRDs) and operator docker images are used in the Helm charts in the [installation](../installation/README.md) folder.


This source code folder also contains a [webhook](webhooks/README.md) that is used to convert between versions of the CRDs and enables the ODA Canvas to support multiple versions of the ODA Component YAML specification.

Finally, there are a number of [utilities](utilities/README.md) that are used to visualize the ODA Components and their logging data.

