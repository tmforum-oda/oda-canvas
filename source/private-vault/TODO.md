# TODOs

- TOC
{:toc}

{{TOC}}

[TOC]

[[_TOC_]]



## Configure Pod-Name-Selector in HC Vault

use  "bound_claims_type": "glob"

https://mec-gitlab.liteon.com/gitlab/help/ci/examples/authenticating-with-hashicorp-vault/index.md#example

### manual try


```
$ vault list auth/jwt-k8s-pv/role

  Keys
  ----
  pv-demoa-comp-one-role
  pv-demob-comp-two-role
```


```
$ vault read -format json auth/jwt-k8s-pv/role/pv-demoa-comp-one-role

{
  "request_id": "e15b105e-b847-f75b-5de2-aeecc76ef4de",
  "lease_id": "",
  "lease_duration": 0,
  "renewable": false,
  "data": {
    "allowed_redirect_uris": [
      "http://canvas-vault-hc.canvas-vault.svc.cluster.local:8200/jwt-test/callback"
    ],
    "bound_audiences": [
      "https://kubernetes.default.svc.cluster.local"
    ],
    "bound_claims": null,
    "bound_claims_type": "string",
    "bound_subject": "system:serviceaccount:demo-comp:default",
    "claim_mappings": null,
    "clock_skew_leeway": 0,
    "expiration_leeway": 0,
    "groups_claim": "",
    "max_age": 0,
    "not_before_leeway": 0,
    "oidc_scopes": null,
    "role_type": "jwt",
    "token_bound_cidrs": [],
    "token_explicit_max_ttl": 0,
    "token_max_ttl": 0,
    "token_no_default_policy": false,
    "token_num_uses": 0,
    "token_period": 0,
    "token_policies": [
      "pv-demoa-comp-one-policy"
    ],
    "token_ttl": 3600,
    "token_type": "default",
    "user_claim": "sub",
    "user_claim_json_pointer": false,
    "verbose_oidc_logging": false
  },
  "warnings": null
}
```

## localhost token negotiation

Not yet implemented.


## port configuration from privatevault

does not work at the moment.

## Change HC Vault DEV Server to standalone with persistence

https://discuss.hashicorp.com/t/dev-mode-with-disk-storage/44805

## Use JWT-AUTH for authenticating the PrivateVault-Operator

Currently the DEV server root password is hard coded in the operator.
Setup an intial JWT Auth for the PrivateVault-Operator ServiceAccount which allows
creating new keystores, policies and jwt-roles.

## refresh token periodically in sidecar

the login is done only once at the startup but should be refreshed before it expires.

## implement otheroptions than sidecar

* env-vars
* file
* k8s-secrets

