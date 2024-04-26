# Install Canvas use case

This use-case describes installation, upgrade and uninstallation of the ODA Canvas.

It uses the following assumptions:

* The ODA Canvas is installed using a package management solution.
* The ODA Canvas can be upgraded without interfering with running ODA Components.
* The ODA Canvas can only be uninstalled if no ODA Components are running.

## Install ODA Canvas

![canvas-install](http://www.plantuml.com/plantuml/proxy?cache=no&src=https://raw.githubusercontent.com/tmforum-oda/oda-canvas/master/usecase-library/pumlFiles/canvas-install.puml)
[plantUML code](pumlFiles/canvas-install.puml)

## Upgrade ODA Canvas

The canvas should support seamless upgrade or downgrade of any of the Canvas Operators without affecting the running components. On upgrade or restart of any operator, the operator should reapply all of its managed resources. The declarative nature of the resources means this re-application will only affect resources that have changed.

## Uninstall ODA Canvas

The uninstallation should use a pre-uninstall hook to check that there are no running ODA Components before proceeding with the uninstallation.
