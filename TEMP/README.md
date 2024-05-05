# Build Component-Operator

```
./TEMP/build/build-component-operator.sh
```

Image: `mtr.devops.telekom.de/magenta_canvas/public:component-istiocontroller-0.4.0-compvault`

# deploy patched canvas from local filesystem 

```
cd ~/git/oda-canvas-component-vault-ODAA26
cd charts/cert-manager-init
helm dependency update
helm dependency build
cd ../../charts/controller
helm dependency update
helm dependency build
cd ../../charts/canvas-oda
helm dependency update
helm dependency build
cd ../..
helm upgrade --install canvas charts/canvas-oda -n canvas --create-namespace --set keycloak.service.type=ClusterIP --set=controller.configmap.loglevel=10 --set=controller.deployment.imagePullPolicy=Always
```

# product catalog with component vault

## deploy PRODCAT

```
helm upgrade --install prodcat -n components --create-namespace feature-definition-and-test-kit/testData/productcatalog-v1beta3-compvault
```

## undeploy PRODCAT

```
helm uninstall prodcat -n components 
```

# ComponentVault Operator

## deploy ComponentVault Operator

```
helm upgrade --install componentvault-operator -n canvas --create-namespace --set=logLevel=10 source/operators/componentvaultoperator-hc/helmcharts/cvop
```


## undeploy ComponentVault Operator

```
helm uninstall -n canvas componentvault-operator
```