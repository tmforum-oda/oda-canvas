# Credentials Management Operator

The Credentials Management Operator is a Kubernetes operator designed for the ODA Canvas Reference Implementation to securely manage and automate the creation and lifecycle management of Kubernetes secrets for components deployed on ODA-Canvas. It leverages Kubernetes and identity platform to handle sensitive information, ensuring secure access with minimal manual intervention.

The operator is built using the Kopf framework.It watches for changes in `identityconfigs` custom resources and handles lifecycle management of Kubernetes secrets accordingly.It interacts with identity platform (e.g. Keycloak) using environment variables for configuration (CLIENT_ID, CLIENT_SECRET, KEYCLOAK_BASE, KEYCLOAK_REALM) which are set via Helm values in [values.yaml](https://github.com/tmforum-oda/oda-canvas/blob/main/charts/credentialsmanagement-operator/values.yaml) or it can be passed during installation of the operator using **--set** option with helm insatall command.

## Installation

1. Clone oda-canvas project

    ```bash
    git clone https://github.com/tmforum-oda/oda-canvas.git
    cd oda-canvas
    ```

2. Install Credentials-Management-Operator
   
    Client for Credentials-Management-Operator is created in IDM through keycloak installation [chart](https://github.com/tmforum-oda/oda-canvas/blob/main/charts/canvas-oda/values.yaml#L124) during keycloak installation. 

    Manually retrieve **secret** of Credentials-Management-Operator **client** `credentialsmanagement-operator` in keycloak and add it in [values.yaml](https://github.com/tmforum-oda/oda-canvas/blob/main/charts/credentialsmanagement-operator/values.yaml) file :
        
     ```yaml
     client_secret: pDWc*****ITn
     ```

     Using updated **values.yaml** file install the operator using the following command.
  
      ```bash
      helm install credman-op charts/credentialsmanagement-operator -n canvas -f values.yaml
      ```
    **"or"**
   
     If you prefer to use the **--set** option instead of editing **values.yaml**.You can add **secret** inline without modifying helm values file:
  
      ```bash
      helm install credman-op charts/credentialsmanagement-operator -n canvas --set=credentials.client_secret=pDWc*****ITn
      ```
   **"or"**
     
     If you want you can also set it as an environment variable and then install the operator using helm install command.
   
      ```bash
      helm install credman-op charts/credentialsmanagement-operator -n canvas
      ```
   


For more details, see the Helm chart documentation in [README.md](https://github.com/tmforum-oda/oda-canvas/blob/main/charts/credentialsmanagement-operator/README.md) and configuration options in [values.yaml](https://github.com/tmforum-oda/oda-canvas/blob/main/charts/credentialsmanagement-operator/values.yaml).
