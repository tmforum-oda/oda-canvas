# Helm Charts

## DependentAPIOperator

### install 

```
helm upgrade --install -n canvas dependent-api-operator helmcharts/dependentAPIOperator
```


### uninstall 

```
helm uninstall -n canvas dependent-api-operator
```


## Product Catalog Component

### install

#### with 1 dependent APIs

```
helm upgrade --install -n components prodcat helmcharts/productcatalog-component
```

#### with 2 dependent APIs

```
helm upgrade --install -n components prodcat helmcharts/productcatalog-component-2depapis
```


### uninstall

```
helm uninstall -n components prodcat 
```

# Logfiles

```
kubectl logs -n canvas deployment/oda-controller-ingress --tail 1 -f
```