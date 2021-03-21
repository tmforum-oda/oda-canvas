#!/bin/bash

echo ""
echo "*********************************************************************"
echo "Configuring Helm repositories"
echo "*********************************************************************"
echo ""

helm repo add stable https://charts.helm.sh/stable
helm repo add codecentric https://codecentric.github.io/helm-charts
helm repo add incubator https://charts.helm.sh/incubator

echo ""
echo "*********************************************************************"
echo "Installing base canvas"
echo "*********************************************************************"
echo ""

helm install canvas canvas/
retVal=$?

if [ $retVal -ne 0 ]; then
    echo ""
    echo "Canvas base install failed"
    exit 1
else
    echo ""
    echo "*********************************************************************"
    echo "Installing Keycloak"
    echo "*********************************************************************"
    echo ""
    helm install --namespace canvas keycloak codecentric/keycloak --set keycloak.ingress.enabled=true
    echo ""
    echo "*********************************************************************"
    echo "Installing Kafka"
    echo "*********************************************************************"
    echo ""
    helm install --namespace canvas kafka incubator/kafka
    echo ""
fi

echo ""
echo "*********************************************************************"
echo "Install script finished"
echo "*********************************************************************"
exit 0

