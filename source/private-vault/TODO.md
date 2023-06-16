# DONE

## Configure Pod-Name-Selector in HC Vault &#x2713;  

HashiCorps Python library "hvac" does not support "user_claim_json_pointer".
PR with support was created: https://github.com/hvac/hvac/pull/998


# TODOs


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

## create PrivateVault CustomResource from in Component Operator

if the format is aligned, the Component-Operator is responsible for creation, updating and deletion of the private-vault custom resource.

## remove default policy

after JWT authenticating the default policy is autmatically added to the pv-(compid)-role policy.

## remove tests methods from pv-operator 

the tests should be extracted into a seperate test file.

## privatevault custom resource does not support update

update is implemented as call to create and this fails, 
when a second time the kv store is created.

