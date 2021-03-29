docker build --file component-IngressController-dockerfile -t tmforumodacanvas/component-controller:0.11.0 -t tmforumodacanvas/component-controller:master .
docker push tmforumodacanvas/component-controller --all-tags
#docker build --file component-wso2Controller-dockerfile -t brianjburton/odacomponentcontroller-wso2:0.9 -t brianjburton/odacomponentcontroller-wso2:latest .
#docker push brianjburton/odacomponentcontroller-wso2  --all-tags
docker build --file securityControllerAPIserver-keycloak-dockerfile -t tmforumodacanvas/security-listener:0.3.0 -t tmforumodacanvas/security-listener:master .
docker push tmforumodacanvas/security-listener  --all-tags
