# Implementation

The webhook requires a TLS certificate. The certificate is created and signed as part of the Canvas Install script. The script puts the tls certificate and key in a secret called `compcrdwebhook-secret`.


## Accessing certificate in NodeJS implementation


The key and certificate are used by the `app.js` implementation 

```
var privateKey  = fs.readFileSync('/etc/secret-volume/tls.key', 'utf8');
var certificate = fs.readFileSync('/etc/secret-volume/tls.crt', 'utf8');
var credentials = {key: privateKey, cert: certificate};
```




## Component Custom Resource reference to webhook

The `oda-component-crd.yaml` file references the webhook, including the caBundle CA bundle retrieved from the k8s API; You can get your cluster’s CA bundle with:

```
kubectl config view --raw --minify --flatten -o jsonpath='{.clusters[].cluster.certificate-authority-data}'
```


The `oda-component-crd.yaml` file has an section that refers to the webhook strategy :

```
  conversion:
    strategy: Webhook
    # webhookClientConfig is required when strategy is `Webhook` and it configures the webhook endpoint to be called by API server.
    webhook:
      conversionReviewVersions: ["v1alpha1", "v1alpha2", "v1alpha3", "v1beta1"]
      clientConfig:
        caBundle: {{ .Values.global.clusterCABundle }}
        service:
          namespace: canvas
          name: compcrdwebhook
          path: /
          port: 443
```

The actual caBundle is added as a Helm value in the `oda-canvas-charts\canvas\values.yaml` file.

