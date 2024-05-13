#!/bin/sh
sudo docker build -t mtr.devops.telekom.de/magenta_canvas/public:dependentapi-simple-operator-0.1.0-rc .
sudo docker push mtr.devops.telekom.de/magenta_canvas/public:dependentapi-simple-operator-0.1.0-rc
