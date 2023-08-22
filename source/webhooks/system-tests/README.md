# System tests

To test as a micro-service in Kubernetes through the Kubernetes API, install the ODA Canvas environment and deploy at least one component. Get local access to the Kubernetes API by creating a proxy:

```
kubectl proxy
```

Then run the tests in the Postman Collection. The Postman tests allow you to request the different Kubernetes resources as specific versions. For example, to request access to the `v1beta2` version of a component, use the following URL:

```
http://{{Hostname}}/apis/oda.tmforum.org/v1beta2/components
```

(If you are running agaist a Rancher managed kubernetes cluster, use the *HostnameforRancher* variable instead of *Hostname*)

If the requested API version is different to the version of the compoent that was deployed, the webhook will be called to perform the translation.

