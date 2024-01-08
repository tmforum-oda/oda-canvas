# Canvas portal

A web ui for Canvas

# How to install

## Prerequisites

- Kubernetes 1.22+
- helm v3+

## Steps

- download the charts

```bash
git clone https://github.com/tmforum-oda/oda-canvas
cd oda-canvas/canvas-portal/
```

- quick install

```bash
helm install canvas-portal ./charts -n components \
--set image.repository=docker.io/wctdevops/canvas-portal \
--set image.tag=20240102 \
--set service.type=NodePort
```

- install with ingress

```bash
helm install canvas-portal ./charts -n components \
--set image.repository=docker.io/wctdevops/canvas-portal \
--set image.tag=20240102 \
--set ingress.enabled=true \
--set ingress.className=nginx \
```

- install with more parameters

```bash
helm install canvas-portal ./charts -n components \
--set image.repository=xx \
--set image.tag=xx \
--set service.type=NodePort \
--set env.portalUsername=admin \
--set env.portalPassword=pAssw0rd \
--set env.helmRepoUrl=xx \
--set env.helmRepoUsername=xx \
--set env.helmRepoPassword=xxx
```

## Parameters and defaults

| Parameter            | Description                                                          | Default   |
|----------------------|----------------------------------------------------------------------|-----------|
| image.repository     | image repository                                                     |           |
| image.tag            | image tag                                                            |           |
| ingress.enabled      | use ingress or not                                                   | false     |
| service.type         | service type                                                         | ClusterIP |
| env.portalUsername   | username of portal                                                   | admin     |
| env.portalPassword   | password of portal                                                   | pAssw0rd  | 
| env.helmRepoUrl      | helm repo for  ODA components                                        |           |
| env.helmRepoUsername | helm repo username                                                   |           |
| env.helmRepoPassword | helm repo password                                                   |           |
 | env.httpLoggingInterceptorLevel | http logging interceptor level, allowed value TRACE,OFF   | TRACE     |

# Uninstall

```bash
helm uninstall canvas-portal -n components
```
