# Upgrade Canvas use case

This use-case describes how a canvas can support seamless upgrade of the underlying component specifications. This is a key requirement for a canvas that is intended to be used in a production environment. The canvas should be able to support the following scenarios:

* As the underlying spec is upgraded, the canvas should be able to support components of different versions. This is to support a phased upgrade of the components. We expact a canvas to support the current and previous two versions (N-2). The canvas must also work with the version prior to that, but with deprecation warnings. e.g. if the underlying spec is at version v1, the canvas should support v1, v1beta4, v1beta3 and v1beta2 (with warnings). 
* The canvas should also support operators using different versions of the underlying spec. e.g. if the underlying spec is at version v1, the canvas should support operators using v1, v1beta4, v1beta3 and v1beta2 (with warnings).

**Note** This use case is separate to the use case for supporting seamless upgrade of the same component. This use case is about supporting different versions of the underlying spec. The use case for supporting upgrades of the same component is described in [UC003](UC003-Configure-Exposed-APIs.md).


## Support components of different versions

![componentsWithDifferentVersions](http://www.plantuml.com/plantuml/proxy?cache=no&src=https://raw.githubusercontent.com/tmforum-oda/oda-canvas/main/usecase-library/pumlFiles/components-with-different-versions.puml)
[plantUML code](pumlFiles/components-with-different-versions.puml)

## Support operators using different versions

![operatorsWithDifferentVersions](http://www.plantuml.com/plantuml/proxy?cache=no&src=https://raw.githubusercontent.com/tmforum-oda/oda-canvas/main/usecase-library/pumlFiles/operators-with-different-versions.puml)
[plantUML code](pumlFiles/operators-with-different-versions.puml)