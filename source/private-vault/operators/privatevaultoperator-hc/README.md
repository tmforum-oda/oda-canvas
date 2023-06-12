# Private Vault Operator using HashiCorp

* https://github.com/hvac/hvac

## initial deploy KOPF Framework

```
helm upgrade --install kopf-framework helmcharts/kopf-framework --namespace privatevault-system --create-namespace
```

## deploy CRDs

```
helm upgrade --install kopf-framework helmcharts/kopf-framework --namespace privatevault-system --create-namespace
```


## deploy PV Operator

```
helm upgrade --install pvop helmcharts/pvop --namespace privatevault-system --create-namespace
```


## uninstall PV Operator

```
helm uninstall pvop -n privatevault-system
helm uninstall kopf-framework -n privatevault-system
kubectl delete ns privatevault-system
```
