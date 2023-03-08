

Installing KOPF (tested in GKE)


sudo pip3 install -r requirements.txt

Test examples at https://github.com/zalando-incubator/kopf/tree/master/examples


* Apply peering.yaml for the CRD's used by kopf
* Apply rbac.yaml to create the service account and roles with the corect permissions
* Apply oda-component-crd.yaml to define the component.oda.tmforum.org CRD
* build the docker image
* Apply the odacontroller-manifest.yaml
* Apply the productCatalog.component.yaml to create the actual component
