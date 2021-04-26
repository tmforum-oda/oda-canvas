# ODA Component webhooks

The Component envelopes are defined by a Kubernetes Custom Resource Definition (CRD) - see https://kubernetes.io/docs/tasks/extend-kubernetes/custom-resources/custom-resource-definitions/. The ODA Component CRD's are installed as part of the Canvas helm chart https://github.com/tmforum-oda/oda-canvas-charts/tree/master/canvas/crds 

As we evolve the Component envelope standard, we will version-control the CRD's following Kubernetes versioning patterns - see https://kubernetes.io/docs/tasks/extend-kubernetes/custom-resources/custom-resource-definition-versioning/

Kubernetes allows you to have multiple versions of the same CRD installed at the same time, and has a well thought-through approach to:
* allowing clients to choose which version they are using, 
* to deprecate and eventually remove support of versions and,
* to convert between different versions. 

Kubernetes always stores the CRD in a preferred version (which is set as part of the CRD definition). If you create a resource with a different version to the preferred version, Kubernetes will convert the versions as it stores the CRD.

The Webhook allows you to create custom code to support Kubernetes in converting between versions. In the CRD definition, you can set a conversion strategy of Webhook and provide details of the service where the webhook API is exposed.

```
  conversion:
    strategy: Webhook
    webhook:
      conversionReviewVersions: ["v1alpha1", "v1alpha2", "v1alpha3", "v1beta1"]
      clientConfig:
        caBundle: LS0tLS1CRUdJTiB--Details Removed--Q0FURS0tLS0tCg==
        service:
          namespace: canvas
          name: compcrdwebhook
          path: /
          port: 443
``` 

