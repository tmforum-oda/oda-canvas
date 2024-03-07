# Testing vault from cli

## Configure Vault address

```
VAULT_ADDR=https://canvas-vault-hc.ihc-dt.cluster-3.de
```

## Login

```
vault login

  Token (will be hidden):
  
  Success! You are now authenticated. The token information displayed below
  is already stored in the token helper. You do NOT need to run "vault login"
  again. Future Vault requests will automatically use this token.
  
  Key                  Value
  ---                  -----
  token                *****
  token_accessor       2i9x8JLm3jam0tViCyy8KEgV
  token_duration       ∞
  token_renewable      false
  token_policies       ["root"]
  identity_policies    []
  policies             ["root"]  
```

## list roles

```
$ vault list auth/jwt-k8s-pv/role

  Keys
  ----
  pv-demoa-comp-one-role
  pv-demob-comp-two-role
```

## details for one role

```
$ vault read auth/jwt-k8s-pv/role/pv-demoa-comp-one-role

	Key                        Value
	---                        -----
	allowed_redirect_uris      [http://canvas-vault-hc.canvas-vault.svc.cluster.local:8200/jwt-test/callback]
	bound_audiences            [https://kubernetes.default.svc.cluster.local]
	bound_claims               map[/kubernetes.io/namespace:demo-comp /kubernetes.io/pod/name:demoa-comp-one-* /kubernetes.io/serviceaccount/name:default]
	bound_claims_type          glob
	bound_subject              n/a
	claim_mappings             <nil>
	clock_skew_leeway          0
	expiration_leeway          0
	groups_claim               n/a
	max_age                    0
	not_before_leeway          0
	oidc_scopes                <nil>
	role_type                  jwt
	token_bound_cidrs          []
	token_explicit_max_ttl     0s
	token_max_ttl              0s
	token_no_default_policy    false
	token_num_uses             0
	token_period               0s
	token_policies             [pv-demoa-comp-one-policy]
	token_ttl                  1h
	token_type                 default
	user_claim                 sub
	user_claim_json_pointer    false
	verbose_oidc_logging       false
```

## list policies

```
$ vault policy list

	default
	pv-demoa-comp-one-policy
	pv-demob-comp-two-policy
	root
```

## get details for a policy

```
$ vault policy read pv-demoa-comp-one-policy

	path "kv-demoa-comp-one/data/sidecar/*" {
          capabilities = ["create", "read", "update", "delete", "list", "patch"]
        }
```

