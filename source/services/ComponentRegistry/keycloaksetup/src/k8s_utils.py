import base64

from kubernetes import client, config
from kubernetes.client.rest import ApiException


def create_or_update_k8s_secret(namespace: str, client_id: str, client_secret: str, token_url: str):
    """
    Creates or updates a Kubernetes Secret with Keycloak client credentials.
    
    Args:
        secret_name: Name of the Kubernetes Secret to create/update
        client_id: Keycloak client ID to store
        client_secret: Keycloak client secret to store
        token_url: Keycloak token URL to get new tokens
    """
    return
    secret_name = f"{client_id}-oidc-secret"
    try:
        # Load Kubernetes configuration
        # This will use in-cluster config if running in a pod, otherwise uses kubeconfig
        try:
            config.load_incluster_config()
            print(f"Using in-cluster Kubernetes configuration")
        except config.ConfigException:
            config.load_kube_config()
            print(f"Using kubeconfig file")
        
        # Create API client
        v1 = client.CoreV1Api()
        
        # Prepare secret data (Kubernetes secrets data must be base64 encoded)
        secret_data = {
            "client_id": base64.b64encode(client_id.encode()).decode(),
            "client_secret": base64.b64encode(client_secret.encode()).decode(),
            "token_url": base64.b64encode(token_url.encode()).decode()
        }
        
        # Create secret metadata
        metadata = client.V1ObjectMeta(
            name=secret_name,
            namespace=namespace,
            labels={
                "app": "componentregistry",
                "managed-by": "keycloak-setup"
            }
        )
        
        # Create secret object
        secret = client.V1Secret(
            api_version="v1",
            kind="Secret",
            metadata=metadata,
            type="Opaque",
            data=secret_data
        )
        
        # Try to update existing secret first
        try:
            v1.read_namespaced_secret(name=secret_name, namespace=namespace)
            # Secret exists, update it
            v1.replace_namespaced_secret(
                name=secret_name,
                namespace=namespace,
                body=secret
            )
            print(f"Updated Kubernetes Secret '{secret_name}' in namespace '{namespace}'")
        except ApiException as e:
            if e.status == 404:
                # Secret doesn't exist, create it
                v1.create_namespaced_secret(
                    namespace=namespace,
                    body=secret
                )
                print(f"Created Kubernetes Secret '{secret_name}' in namespace '{namespace}'")
            else:
                raise
                
    except Exception as e:
        print(f"Error creating/updating Kubernetes Secret '{secret_name}': {str(e)}")
        raise