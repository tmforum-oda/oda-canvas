import kopf
import kubernetes.client
import logging
from kubernetes.client.rest import ApiException
import os
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
from azure.mgmt.apimanagement import ApiManagementClient
from azure.mgmt.apimanagement.models import (
    ApiCreateOrUpdateParameter,
    AuthenticationSettingsContract,
    OpenIdConnectProviderContract
)
from azure.core.exceptions import AzureError, ResourceNotFoundError

# Configure logging level based on environment variable, default to INFO
logging_level_str = os.environ.get("LOGGING", 'INFO')
logging_level = getattr(logging, logging_level_str.upper(), logging.INFO)
logger = logging.getLogger("APIOperator")
logger.setLevel(logging_level)

# Custom Resource Definition (CRD) group, version, and plural
GROUP = "oda.tmforum.org"
VERSION = "v1beta3"
APIS_PLURAL = "exposedapis"

# Kubernetes API groups for networking resources
NETWORKING_GROUP = "networking.k8s.io"
NETWORKING_VERSION = "v1"
INGRESS_PLURAL = "ingresses"

# Azure Key Vault setup
KEY_VAULT_NAME = os.getenv('KEY_VAULT_NAME')
if not KEY_VAULT_NAME:
    raise ValueError("Environment variable 'KEY_VAULT_NAME' is not set.")
KV_URI = f"https://{KEY_VAULT_NAME}.vault.azure.net"

# Azure credentials using DefaultAzureCredential, which supports multiple authentication methods
credential = DefaultAzureCredential()

# Initialize Key Vault client
kv_client = SecretClient(vault_url=KV_URI, credential=credential)

# Retrieve secrets from Key Vault
try:
    APIM_SERVICE_NAME = kv_client.get_secret("apim-service-name").value
    RESOURCE_GROUP = kv_client.get_secret("resource-group").value
    SUBSCRIPTION_ID = kv_client.get_secret("subscription-id").value
    AAD_TENANT_ID = kv_client.get_secret("aad-tenant-id").value
    AAD_CLIENT_ID = kv_client.get_secret("aad-client-id").value
except AzureError as e:
    logger.error(f"Error accessing Azure Key Vault: {e}")
    raise
    
required_secrets = {
    'APIM_SERVICE_NAME': APIM_SERVICE_NAME,
    'RESOURCE_GROUP': RESOURCE_GROUP,
    'SUBSCRIPTION_ID': SUBSCRIPTION_ID,
    'AAD_TENANT_ID': AAD_TENANT_ID,
    'AAD_CLIENT_ID': AAD_CLIENT_ID
}

missing_secrets = [key for key, value in required_secrets.items() if not value]
if missing_secrets:
    raise ValueError(f"Missing secrets in Key Vault: {', '.join(missing_secrets)}")

# Initialize Azure API Management client
apim_client = ApiManagementClient(credential, SUBSCRIPTION_ID)

# OpenID Connect Provider details for Azure Active Directory integration
OPENID_PROVIDER_NAME = "AzureAD"
OPENID_METADATA_ENDPOINT = f"https://login.microsoftonline.com/{AAD_TENANT_ID}/v2.0/.well-known/openid-configuration"
OPENID_CLIENT_ID = AAD_CLIENT_ID

def create_openid_connect_provider():
    """
    Ensures that the OpenID Connect Provider is configured in Azure API Management.
    This is necessary for enabling OAuth 2.0 authentication using Azure Active Directory.

    Raises:
        AzureError: If there is an error configuring the OpenID Connect Provider in APIM.
    """
    try:
        provider = OpenIdConnectProviderContract(
            display_name="Azure AD",
            description="Azure Active Directory OpenID Connect Provider",
            metadata_endpoint=OPENID_METADATA_ENDPOINT,
            client_id=OPENID_CLIENT_ID
        )
        apim_client.open_id_connect_provider.create_or_update(
            resource_group_name=RESOURCE_GROUP,
            service_name=APIM_SERVICE_NAME,
            opid=OPENID_PROVIDER_NAME,
            parameters=provider
        )
        logger.info("OpenID Connect Provider configured in APIM.")
    except AzureError as e:
        logger.error(f"Error configuring OpenID Connect Provider: {e}")
        raise

# Call the function to ensure the OpenID Connect Provider is set up
create_openid_connect_provider()

@kopf.on.create(GROUP, VERSION, APIS_PLURAL, retries=5)
@kopf.on.update(GROUP, VERSION, APIS_PLURAL, retries=5)
def manage_api_lifecycle(spec, name, namespace, status, meta, **kwargs):
    """
    Handles the creation and update events for the custom resource representing an API.
    This function manages the lifecycle by:
    - Creating or updating the Ingress resource to expose the service.
    - Configuring the API in Azure API Management.
    - Applying policies such as JWT validation, rate limiting, and CORS.

    Args:
        spec (dict): The specification of the custom resource.
        name (str): The name of the custom resource.
        namespace (str): The namespace where the custom resource is deployed.
        status (dict): The status subresource of the custom resource.
        meta (dict): Metadata of the custom resource.
        **kwargs: Additional keyword arguments.
    """
    # Extract API specifications from the custom resource
    api_spec = {
        "path": spec.get("path"),
        "name": name,
        "specification": spec.get("specification"),
        "implementation": spec.get("implementation"),
        "port": spec.get("port"),
        "rateLimit": spec.get("rateLimit", {}),
        "CORS": spec.get("CORS", {})
    }

    logger.info(f"Processing API resource '{name}' in namespace '{namespace}'.")

    # Check if the API is already configured with the same spec to avoid unnecessary updates
    if status and status.get('apimBind', {}).get('spec') == api_spec:
        logger.info(f"API '{name}' is already bound with the same spec. Skipping update.")
        return

    # Create or update the Ingress resource to expose the service
    ingress_created = create_or_update_ingress(spec, name, namespace, meta)
    if not ingress_created:
        logger.error("Ingress creation/update failed. Skipping APIM update.")
        return

    # Update Azure API Management with the new API configuration
    try:
        update_apim(api_spec, namespace)
        logger.info(f"API '{name}' successfully configured in Azure APIM.")
    except Exception as e:
        logger.error(f"Error updating Azure APIM for API '{name}': {e}")
        raise kopf.TemporaryError(f"Failed to configure API '{name}' in Azure APIM.")

    # Update the status of the custom resource to reflect the successful operation
    try:
        api_client = kubernetes.client.CustomObjectsApi()
        group = GROUP
        version = VERSION
        plural = APIS_PLURAL
        api_obj = api_client.get_namespaced_custom_object(group, version, namespace, plural, name)

        # Update status
        api_obj.setdefault('status', {})
        api_obj['status']['apimBind'] = {"spec": api_spec}
        api_obj['status']['implementation'] = {"ready": True}
        
        api_client.patch_namespaced_custom_object_status(group, version, namespace, plural, name, {"status": api_obj['status']})

        logger.info(f"Status updated for API resource '{name}'.")
    except ApiException as e:
        logger.error(f"Error updating status for API '{name}': {e}")
        raise kopf.TemporaryError(f"Failed to update status for API '{name}'.")

@kopf.on.delete(GROUP, VERSION, APIS_PLURAL, retries=1)
def manage_api_deletion(meta, name, namespace, **kwargs):
    """
    Handles the deletion event of the custom resource representing an API.
    This function cleans up resources by:
    - Deleting the Ingress resource associated with the API.
    - Removing the API configuration from Azure API Management.

    Args:
        meta (dict): Metadata of the custom resource.
        name (str): The name of the custom resource.
        namespace (str): The namespace where the custom resource was deployed.
        **kwargs: Additional keyword arguments.
    """
    logger.info(f"ExposedAPI '{name}' deleted from namespace '{namespace}'.")

    # Delete the Ingress resource associated with the API
    delete_ingress(name, namespace)

    try:
        existing_api = apim_client.api.get(
            resource_group_name=RESOURCE_GROUP,
            service_name=APIM_SERVICE_NAME,
            api_id=name
        )
        etag = existing_api.etag
    except ResourceNotFoundError:
        logger.info(f"API '{name}' not found in Azure APIM. It may have already been deleted.")
        return


    # Remove the API from Azure API Management
    try:
        apim_client.api.delete(
            resource_group_name=RESOURCE_GROUP,
            service_name=APIM_SERVICE_NAME,
            api_id=name,
            if_match=etag
        )
        logger.info(f"API '{name}' deleted from Azure APIM.")
    except AzureError as e:
        logger.error(f"Error deleting API '{name}' from Azure APIM: {e}")
        raise kopf.TemporaryError(f"Failed to delete API '{name}' from Azure APIM.")

def create_or_update_ingress(spec, name, namespace, meta, **kwargs):
    """
    Creates or updates a Kubernetes Ingress resource to expose the service externally.
    The Ingress routes traffic from the cluster ingress controller to the service.

    Args:
        spec (dict): The specification of the custom resource.
        name (str): The name of the custom resource.
        namespace (str): The namespace where the custom resource is deployed.
        meta (dict): Metadata of the custom resource.
        **kwargs: Additional keyword arguments.

    Returns:
        bool: True if the Ingress was successfully created or updated, False otherwise.
    """
    api_instance = kubernetes.client.NetworkingV1Api()
    ingress_name = f"apim-api-ingress-{name}"
    service_name = spec.get("implementation") or name
    service_port = spec.get("port") or 80
    path = spec.get("path") or "/"
    ingress_namespace = namespace

    # Create the Ingress manifest
    ingress_manifest = {
        "apiVersion": f"{NETWORKING_GROUP}/{NETWORKING_VERSION}",
        "kind": "Ingress",
        "metadata": {
            "name": ingress_name,
            "namespace": ingress_namespace,
            "annotations": {
                # Annotations for Azure Application Gateway Ingress Controller can be added here if needed
                # Example: "kubernetes.io/ingress.class": "azure/application-gateway",
            },
        },
        "spec": {
            "ingressClassName": "istio",  # or your specific ingress class
            "rules": [
                {
                    "http": {
                        "paths": [
                            {
                                "path": path,
                                "pathType": "Prefix",
                                "backend": {
                                    "service": {
                                        "name": service_name,
                                        "port": {
                                            "number": int(service_port)
                                        }
                                    }
                                }
                            }
                        ]
                    }
                }
            ]
        }
    }

    # Adopt the resource to ensure proper ownership and garbage collection
    kopf.adopt(ingress_manifest)

    try:
        # Check if the Ingress already exists
        existing_ingress = api_instance.read_namespaced_ingress(
            name=ingress_name,
            namespace=ingress_namespace
        )
        ingress_manifest["metadata"]["resourceVersion"] = existing_ingress.metadata.resource_version
        # Update the existing Ingress
        api_instance.replace_namespaced_ingress(
            name=ingress_name,
            namespace=ingress_namespace,
            body=ingress_manifest
        )
        logger.info(f"Ingress '{ingress_name}' updated successfully in namespace '{ingress_namespace}'.")
        return True
    except ApiException as e:
        if e.status == 404:
            # Create the Ingress if it does not exist
            api_instance.create_namespaced_ingress(
                namespace=ingress_namespace,
                body=ingress_manifest
            )
            logger.info(f"Ingress '{ingress_name}' created successfully in namespace '{ingress_namespace}'.")
            return True
        else:
            logger.error(f"API exception when accessing Ingress: {e}")
            return False

def delete_ingress(name, namespace):
    """
    Deletes the Kubernetes Ingress resource associated with the API.

    Args:
        name (str): The name of the custom resource.
        namespace (str): The namespace where the custom resource was deployed.
    """
    api_instance = kubernetes.client.NetworkingV1Api()
    ingress_name = f"apim-api-ingress-{name}"
    ingress_namespace = namespace

    try:
        api_instance.delete_namespaced_ingress(
            name=ingress_name,
            namespace=ingress_namespace
        )
        logger.info(f"Ingress '{ingress_name}' deleted from namespace '{ingress_namespace}'.")
    except ApiException as e:
        if e.status == 404:
            logger.info(f"Ingress '{ingress_name}' already deleted.")
        else:
            logger.error(f"Error deleting Ingress '{ingress_name}': {e}")
            raise kopf.TemporaryError(f"Failed to delete Ingress '{ingress_name}'.")

def update_apim(api_spec, namespace):
    """
    Creates or updates the API configuration in Azure API Management.
    It includes setting up the API backend, OpenAPI specification, and applying policies.

    Args:
        api_spec (dict): The API specifications extracted from the custom resource.
        namespace (str): The namespace where the custom resource is deployed.

    Raises:
        AzureError: If there is an error interacting with Azure services.
        Exception: For general exceptions during the update process.
    """
    try:
        api_name = api_spec['name']
        path = api_spec['path']
        openapi_spec = api_spec.get('specification')
        if not openapi_spec:
            raise ValueError("API specification is missing.")

        # Get the backend service URL from the Ingress
        ingress_url = get_ingress_url(api_name, namespace, path)

        # Create or update the API in Azure API Management
        api_parameters = ApiCreateOrUpdateParameter(
            display_name=api_name,
            description=f"API for {api_name}",
            path=path,
            protocols=["https"],
            authentication_settings=AuthenticationSettingsContract(
                openid={
                    "openidProviderId": OPENID_PROVIDER_NAME,
                    "bearerTokenSendingMethods": ["authorizationHeader"]
                }
            ),
            subscription_key_parameter_names=None,
            is_current=True,
            value=openapi_spec,
            format="openapi+json",
            service_url=ingress_url  # Set the backend service URL
        )
        
        # Retrieve the existing API to get the ETag
        try:
            existing_api = apim_client.api.get(
            resource_group_name=RESOURCE_GROUP,
            service_name=APIM_SERVICE_NAME,
            api_id=api_name
            )
            etag = existing_api.etag
        except azure.core.exceptions.ResourceNotFoundError:
            etag = None

        # Use the ETag in the create_or_update call
        if etag is None:
            # Create new API without if_match
            apim_client.api.create_or_update(
                resource_group_name=RESOURCE_GROUP,
                service_name=APIM_SERVICE_NAME,
                api_id=api_name,
                parameters=api_parameters
            )
        else:
            # Update existing API with if_match
            apim_client.api.create_or_update(
                resource_group_name=RESOURCE_GROUP,
                service_name=APIM_SERVICE_NAME,
                api_id=api_name,
                parameters=api_parameters,
                if_match=etag
           )
        
        logger.info(f"API '{api_name}' created/updated in Azure APIM.")

        # Configure policies such as JWT validation, rate limiting, and CORS
        configure_apim_policies(api_name, api_spec)
    except AzureError as e:
        logger.error(f"Azure error during APIM update: {e}")
        raise
    except Exception as e:
        logger.error(f"Error updating Azure APIM: {e}")
        raise

def configure_apim_policies(api_id, api_spec):
    """
    Configures policies for the API in Azure API Management.
    Policies include JWT validation, rate limiting, and CORS.

    Args:
        api_id (str): The identifier of the API in APIM.
        api_spec (dict): The API specifications including policy configurations.

    Raises:
        AzureError: If there is an error configuring policies in Azure APIM.
        Exception: For general exceptions during the policy configuration process.
    """
    try:
        # Extract rate limit and CORS configurations from the spec
        rate_limit_config = api_spec.get('rateLimit', {})
        cors_config = api_spec.get('CORS', {})

        # Rate Limiting settings with defaults
        rate_limit_calls = rate_limit_config.get('limit', 100)  # Default to 100 calls
        rate_limit_period = rate_limit_config.get('period', 60)  # Default to 60 seconds

        # CORS settings with defaults
        cors_allowed_origins = cors_config.get('allowOrigins', ['*'])
        cors_allowed_methods = cors_config.get('allowMethods', ['*'])
        cors_allowed_headers = cors_config.get('allowHeaders', ['*'])
        cors_expose_headers = cors_config.get('exposeHeaders', ['*'])
        cors_max_age = cors_config.get('maxAge', 3600)  # Default to 1 hour
        cors_allow_credentials = cors_config.get('allowCredentials', False)

        # Construct the policies XML
        policy_xml = textwrap.dedent(f'''\
        <policies>
            <inbound>
                <base />

                <!-- JWT Validation Policy -->
                <validate-jwt header-name="Authorization"
                              failed-validation-httpcode="401"
                              failed-validation-error-message="Unauthorized. Access token is missing or invalid."
                              require-expiration-time="true"
                              require-scheme="Bearer"
                              require-signed-tokens="true">
                    <openid-config url="{OPENID_METADATA_ENDPOINT}" />
                    <required-claims>
                        <claim name="aud">
                            <value>{AAD_CLIENT_ID}</value>
                        </claim>
                    </required-claims>
                </validate-jwt>

                <!-- Rate Limiting Policy -->
                <rate-limit-by-key calls="{rate_limit_calls}"
                                   renewal-period="{rate_limit_period}"
                                   counter-key="@(context.Request.IpAddress)" />

                <!-- CORS Policy -->
                <cors>
                    <allowed-origins>
                        {''.join(f'<origin>{origin}</origin>' for origin in cors_allowed_origins)}
                    </allowed-origins>
                    <allowed-methods>
                        {''.join(f'<method>{method}</method>' for method in cors_allowed_methods)}
                    </allowed-methods>
                    <allowed-headers>
                        {''.join(f'<header>{header}</header>' for header in cors_allowed_headers)}
                    </allowed-headers>
                    <expose-headers>
                        {''.join(f'<header>{header}</header>' for header in cors_expose_headers)}
                    </expose-headers>
                    <max-age>{cors_max_age}</max-age>
                    <allow-credentials>{"true" if cors_allow_credentials else "false"}</allow-credentials>
                </cors>
            </inbound>
            <backend>
                <base />
            </backend>
            <outbound>
                <base />
            </outbound>
            <on-error>
                <base />
            </on-error>
        </policies>
        ''')

        # Update the API policies in Azure APIM
        apim_client.api_policy.create_or_update(
            resource_group_name=RESOURCE_GROUP,
            service_name=APIM_SERVICE_NAME,
            api_id=api_id,
            parameters={"format": "rawxml", "value": policy_xml}
        )
        logger.info(f"Policies applied to API '{api_id}' in Azure APIM.")
    except AzureError as e:
        logger.error(f"Azure error during APIM policy configuration: {e}")
        raise
    except Exception as e:
        logger.error(f"Error configuring Azure APIM policies: {e}")
        raise Exception(f"Failed to configure policies for API '{api_id}'.") from e        

def get_ingress_url(api_name, namespace, path):
    """
    Retrieves the external URL of the Ingress associated with the API.
    This URL is used as the backend service URL in Azure API Management.

    Args:
        api_name (str): The name of the API.
        namespace (str): The namespace where the Ingress is deployed.
        path (str): The path for the API.

    Returns:
        str: The external URL of the Ingress.

    Raises:
        ApiException: If there is an error retrieving the Ingress.
        ValueError: If the Ingress does not have a load balancer IP or hostname.
    """
    try:
        api_instance = kubernetes.client.NetworkingV1Api()
        ingress_name = f"apim-api-ingress-{api_name}"
        ingress_namespace = namespace

        ingress = api_instance.read_namespaced_ingress(
            name=ingress_name,
            namespace=ingress_namespace
        )

        if ingress.status.load_balancer.ingress:
            lb_ingress = ingress.status.load_balancer.ingress[0]
            host = lb_ingress.hostname or lb_ingress.ip
            if not host:
                raise ValueError("Ingress host not found.")
            # Construct the backend URL            
            scheme = 'https' if ingress.spec.tls else 'http'
            backend_url = f"{scheme}://{host}{path}"
            logger.info(f"Ingress URL for API '{api_name}': {backend_url}")
            return backend_url
        else:
            raise ValueError("Ingress does not have an associated load balancer IP or hostname.")
    except ApiException as e:
        logger.error(f"Error retrieving Ingress URL for API '{api_name}': {e}")
        raise
