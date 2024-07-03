# HashiCorp Vault installation

The provided setup script installs HashiCorp Vault in DEV mode for easy testing.
There is no persistence. So, if the vault POD is restarted all secrets and configurations are lost.

After successful startup the script configures an JWT endpoint to setup a trust relationship to the cluster issuer.
This is differs based on the target environment. 
If no target environment is given, GCP is used.
Details can be found here:
https://developer.hashicorp.com/vault/docs/auth/jwt/oidc-providers/kubernetes#using-service-account-issuer-discovery

Additionally an Istio VirtualService can be created if the domain-name is set for the variable "$CANVASVAULT_VS_HOSTNAME"

Additional the name of the authentication path and the dev root token can be configured using environment variables:

* AUTH_PATH
* VAULT_DEV_ROOT_TOKEN_ID
