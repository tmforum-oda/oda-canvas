#! /bin/sh

# Create tls certificate and key, sign using kubernetes csr and store in kubernetes secret.
# based on the script at https://github.com/alex-leonhardt/k8s-mutate-webhook/blob/master/ssl/ssl.sh

set -o errexit

echo "Exporting variables"

export APP="compcrdwebhook"
export NAMESPACE="canvas"
export CSR_NAME="compcrdwebhook.canvas.svc"

echo "creating certificate"

kubectl apply -n ${NAMESPACE} -f  <(echo "
apiVersion: cert-manager.io/v1alpha2
kind: Certificate
metadata:
  name: ${CSR_NAME}
  namespace: ${NAMESPACE}
spec:
  secretName: ${CSR_NAME}-tls
  keyAlgorithm: rsa
  keySize: 2048
  commonName: ${CSR_NAME}
  isCA: false
  usages:
    - digital signature
    - content commitment # replaces nonRepudiation
    - key encipherment
    - server auth
  dnsNames:
  - ${APP}
  - ${APP}.${NAMESPACE}
  - ${CSR_NAME}
  - ${CSR_NAME}.cluster.local
  issuerRef:
    name: selfsigned-issuer
")



echo "... creating ${app}.pem cert file, key and cabundle"

kubectl -n ${NAMESPACE} get secret ${CSR_NAME}-tls -o jsonpath='{.data.ca\.crt}'  > cabundle.pem.b64
kubectl -n ${NAMESPACE} get secret ${CSR_NAME}-tls -o jsonpath='{.data.tls\.crt}' | base64 -d > ${APP}.pem
kubectl -n ${NAMESPACE} get secret ${CSR_NAME}-tls -o jsonpath='{.data.tls\.key}' | base64 -d > ${APP}.key


echo "... deleting old kubernetes secret"
kubectl delete secret ${APP}-secret --namespace ${NAMESPACE} || :
echo "... creating kubernetes secret"
kubectl create secret tls ${APP}-secret   --cert=./${APP}.pem   --key=./${APP}.key   --namespace ${NAMESPACE}

echo "... deleting temp files"

rm ./${APP}.pem
rm ./${APP}.key
#rm ./cabundle.pem.b64