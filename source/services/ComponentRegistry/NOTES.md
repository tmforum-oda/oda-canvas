# deploy kc init compreg

```
cd %USERPROFILE%/git/oda-canvas
helm upgrade --install  kc-init-compreg -n canvas source/services/ComponentRegistry/keycloaksetup/helm --debug
```

uninstall 

```
helm uninstall -n canvas kc-init-compreg

```
