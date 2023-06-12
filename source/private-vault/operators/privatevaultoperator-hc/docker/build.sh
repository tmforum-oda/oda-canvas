#!/bin/sh
sudo docker build -t mtr.devops.telekom.de/magenta_canvas/private-vault-operator:0.1.0 .
sudo docker push mtr.devops.telekom.de/magenta_canvas/private-vault-operator:0.1.0
