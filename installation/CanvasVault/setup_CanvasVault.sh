#!/bin/bash


export AUTH_PATH="jwt-k8s-sman"
export VAULT_DEV_ROOT_TOKEN_ID="egalegal"
# optional create istio ingress virtualservice when hostname is set
export CANVASVAULT_VS_HOSTNAME="canvas-vault-hc.ihc-dt.cluster-3.de"




set -e

cd $(dirname -- $0)


Y='\033[0;33m'
NC='\033[0m' # No Color

TARGETENV="$1"
if [ -z "$TARGETENV" ]; then
	echo "COMMAND [AWS|GCP|VPS]"
	echo ""
    echo "  using GCP target as default"
    TARGETENV="GCP"
fi

if ([ "$TARGETENV" != "AWS" ] && [ "$TARGETENV" != "GCP" ] && [ "$TARGETENV" != "VPS" ]) ; then
	echo "COMMAND [AWS|GCP|VPS]"
	echo ""
	echo "Deploy and configure HashiCorp Vault as canvas vault"
    exit 1
fi

SRCDIR=.
BASEDIR=`pwd`

if [ ! -d $SRCDIR ]; then
	echo "Please check source directory (${SRCDIR})"
	exit 1
fi

cd $SRCDIR

echo -e "${Y}Deploy and configure HashiCorp Vault (in DEV mode)${NC}"
echo -e "${Y}Installing HashiCorp Vault in DEV mode${NC}"
helm repo add hashicorp https://helm.releases.hashicorp.com
helm repo update
helm upgrade --install canvas-vault-hc hashicorp/vault --version 0.25.0  --namespace canvas-vault --create-namespace --values ./values.yaml --set=server.dev.devRootToken=$VAULT_DEV_ROOT_TOKEN_ID --wait
             

echo "waiting up to 30 seconds for the vault to be ready"
kubectl -n canvas-vault wait -l  statefulset.kubernetes.io/pod-name=canvas-vault-hc-0 --for=condition=ready pod --timeout=30s


if [ -n "$CANVASVAULT_VS_HOSTNAME" ]; then
  echo -e "${Y}Creating public route to canvas vault${NC}"
  cat canvas-vault-hc-vs.yaml.template | envsubst | kubectl apply -f -
fi


echo -e "${Y}Configuring HashiCorp Vault to accept K8S Service Account Issuer${NC}"
X=`kubectl exec -n canvas-vault -it canvas-vault-hc-0 -- vault auth list | grep "$AUTH_PATH" || true`
if [ "$X" == "" ] ; then
    echo -e "\t${Y}exec vault enable${NC}"
    kubectl exec -n canvas-vault -it canvas-vault-hc-0 -- vault auth enable -path "$AUTH_PATH" jwt
else
	echo -e "\t${Y}auth method $AUTH_PATH already enabled${NC}"
fi

# see also: https://developer.hashicorp.com/vault/docs/auth/jwt/oidc-providers/kubernetes#using-service-account-issuer-discovery
CRB=`kubectl get clusterrolebinding oidc-reviewer 2>/dev/null | grep "service-account-issuer-discovery" || true`
if [ "$CRB" == "" ]; then
    echo -e "\t${Y}create cluster role binding oidc-reviewer${NC}"
    kubectl create clusterrolebinding oidc-reviewer  --clusterrole=system:service-account-issuer-discovery --group=system:unauthenticated
else 
    echo -e "\t${Y}cluster role binding oidc-reviewer already exits${NC}"
fi

echo -e "\t${Y}exec vault write oidc_discovery_url${NC}"
if [ "$TARGETENV" == "AWS" ]; then
# setup on AWS
    kubectl exec -n canvas-vault -it canvas-vault-hc-0 -- vault write auth/$AUTH_PATH/config oidc_discovery_url=https://kubernetes.default.svc.cluster.local oidc_discovery_ca_pem=@/var/run/secrets/kubernetes.io/serviceaccount/ca.crt
    ##old kubectl exec -n canvas-vault -it canvas-vault-hc-0 -- vault write auth/$AUTH_PATH/config oidc_discovery_url=https://container.googleapis.com/v1/projects/tmforum-oda-component-cluster/locations/europe-west3/clusters/ihc-dt oidc_discovery_ca_pem=@/var/run/secrets/kubernetes.io/serviceaccount/ca.crt
fi
if [ "$TARGETENV" == "GCP" ]; then
    # setup on GCP
    ISSUER="$(kubectl get --raw /.well-known/openid-configuration | jq -r '.issuer')"
    kubectl exec -n canvas-vault -it canvas-vault-hc-0 -- vault write auth/$AUTH_PATH/config oidc_discovery_url=$ISSUER
fi
if [ "$TARGETENV" == "VPS" ]; then
    # setup on VPS
    ISSUER="$(kubectl get --raw /.well-known/openid-configuration | jq -r '.issuer')"
    kubectl exec -n canvas-vault -it canvas-vault-hc-0 -- vault write auth/$AUTH_PATH/config oidc_discovery_url=$ISSUER oidc_discovery_ca_pem=@/var/run/secrets/kubernetes.io/serviceaccount/ca.crt 
fi

cd $BASEDIR

