# Implementation

The webhook requires a TLS certificate. To create the certificate accepted by Kubernetes follow the commands below (based on the script at https://github.com/alex-leonhardt/k8s-mutate-webhook/blob/master/ssl/ssl.sh).


```
/bin/bash ssl.sh compcrdwebhook canvas
```

This will generate 3 files: compcrdwebhook.csr (certificate request), compcrdwebhook.key (private key), compcrdwebhook.pem (certificate)

The key and certificate are used by the `app.js` implementation 

```
var privateKey  = fs.readFileSync('./compcrdwebhook.key', 'utf8');
var certificate = fs.readFileSync('./compcrdwebhook.pem', 'utf8');
var credentials = {key: privateKey, cert: certificate};
```

You then update the `oda-component-crd.yaml` file to reference the webhook, including the 

```
  conversion:
    strategy: Webhook
    # webhookClientConfig is required when strategy is `Webhook` and it configures the webhook endpoint to be called by API server.
    webhook:
      conversionReviewVersions: ["v1alpha1", "v1alpha2", "v1alpha3", "v1beta1"]
      clientConfig:
        caBundle: LS0tLS1CRUdJTiBDRVJUSUZJQ0F---Insert Real CA Bundle here---JUSUZJQ0FURS0tLS0tCg==
        service:
          namespace: canvas
          name: compcrdwebhook
          path: /
          port: 443
```


The `caBundle:` above refers to the actual CA bundle retrieved from the k8s API, replace it with your own; you can get your cluster’s CA bundle with:

```
kubectl config view --raw --minify --flatten -o jsonpath='{.clusters[].cluster.certificate-authority-data}'
```
