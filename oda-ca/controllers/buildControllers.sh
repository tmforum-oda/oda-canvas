docker build --file component-IngressController-dockerfile -t brianjburton/odacomponentcontroller-ingress:0.11.0 -t brianjburton/odacomponentcontroller-ingress:latest .
docker push brianjburton/odacomponentcontroller-ingress --all-tags
#docker build --file component-wso2Controller-dockerfile -t brianjburton/odacomponentcontroller-wso2:0.9 -t brianjburton/odacomponentcontroller-wso2:latest .
#docker push brianjburton/odacomponentcontroller-wso2  --all-tags
docker build --file securityControllerAPIserver-keycloak-dockerfile -t brianjburton/odaseccon-keycloak:0.3.0 -t brianjburton/odaseccon-keycloak:latest .
docker push brianjburton/odaseccon-keycloak  --all-tags
