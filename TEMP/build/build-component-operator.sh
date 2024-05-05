#!/bin/sh

cd $(dirname -- $0)

cd ../../source/operators
sudo docker build -t mtr.devops.telekom.de/magenta_canvas/public:component-istiocontroller-0.4.0-compvault -f component-IstioController-dockerfile .
sudo docker push mtr.devops.telekom.de/magenta_canvas/public:component-istiocontroller-0.4.0-compvault

kubectl rollout restart deployment -n canvas oda-controller-ingress
