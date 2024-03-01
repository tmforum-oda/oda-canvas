#!/bin/sh
sudo docker build -t mtr.devops.telekom.de/magenta_canvas/component-vault-operator:0.1.1 .
sudo docker push mtr.devops.telekom.de/magenta_canvas/component-vault-operator:0.1.1
