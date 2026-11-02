# Component-Registry Documentation

## Prerequisites

ODA Canvas is installed with default values.  
compreg not yet released?  
So, install from main branch neccessary.


## Port-Forward Component-Registry UI

```
kubectl port-forward -n canvas svc/canvas-compreg 8080:80
```

Open UI in Browser:

http://localhost:8080

![Empty Component-Registry](images/compreg-01-empty.png)


## Deploy ODA Component r-cat

```
helm upgrade --install r-cat -n components --create-namespace feature-definition-and-test-kit/testData/productcatalog-v1
```

After a few seconds the UI shows the new ODA Component r-cat:

![r-cat](images/compreg-02-r-cat.png)


