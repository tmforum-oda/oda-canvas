import kopf
import kubernetes.client
import logging
import textwrap # I noticed this was missing in the original file, it's needed for the policy XML
from kubernetes.client.rest import ApiException
import os
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
from azure.mgmt.apimanagement import ApiManagementClient
from azure.mgmt.apimanagement.models import (
    ApiCreateOrUpdateParameter,
    AuthenticationSettingsContract,
    OpenIdConnectProviderContract,
    PolicyContract, NamedValueCreateContract
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

# Kubernetes API groups
NETWORKING_GROUP = "networking.k8s.io"
NETWORKING_VERSION = "v1"
INGRESS_PLURAL = "ingresses"


#CORE_API_VERSION = "v1"
#APPS_API_VERSION = "v1"

# Azure Key Vault setup
KEY_VAULT_NAME = os.getenv('KEY_VAULT_NAME')
if not KEY_VAULT_NAME:
    raise ValueError("Environment variable 'KEY_VAULT_NAME' is not set.")
KV_URI = f"https://{KEY_VAULT_NAME}.vault.azure.net"

# Azure credentials
credential = DefaultAzureCredential()
kv_client = SecretClient(vault_url=KV_URI, credential=credential)

# Retrieve secrets
try:
    APIM_SERVICE_NAME = kv_client.get_secret("apim-service-name").value
    RESOURCE_GROUP = kv_client.get_secret("resource-group").value
    SUBSCRIPTION_ID = kv_client.get_secret("subscription-id").value
    AAD_TENANT_ID = kv_client.get_secret("aad-tenant-id").value
    AAD_CLIENT_ID = kv_client.get_secret("aad-client-id").value
    APP_INSIGHTS_KEY = kv_client.get_secret("app-insights-instrumentation-key").value
except AzureError as e:
    logger.error(f"Error accessing Azure Key Vault: {e}")
    raise
    
required_secrets = {
    'APIM_SERVICE_NAME': APIM_SERVICE_NAME,
    'RESOURCE_GROUP': RESOURCE_GROUP,
    'SUBSCRIPTION_ID': SUBSCRIPTION_ID,
    'AAD_TENANT_ID': AAD_TENANT_ID,
    'AAD_CLIENT_ID': AAD_CLIENT_ID,
    'APP_INSIGHTS_KEY': APP_INSIGHTS_KEY
}
if not all(required_secrets.values()):
    raise ValueError(f"Missing one or more required secrets in Key Vault: {', '.join(k for k, v in required_secrets.items() if not v)}")

apim_client = ApiManagementClient(credential, SUBSCRIPTION_ID)

# OpenID Connect Provider details
OPENID_PROVIDER_NAME = "AzureAD"
OPENID_METADATA_ENDPOINT = f"https://login.microsoftonline.com/{AAD_TENANT_ID}/v2.0/.well-known/openid-configuration"
OPENID_CLIENT_ID = AAD_CLIENT_ID


# NEW: Function to configure APIM tracing backend
def configure_apim_observability_backend():
    """
    Ensures that APIM is configured with a logger pointing to Application Insights
    and a named value for the instrumentation key.
    """
    logger_name = "appinsights-logger"
    named_value_name = "AppInsightsInstrumentationKey"

    try:
        # 1. Create the Application Insights Logger in APIM
        logger_params = {
            "logger_type": "applicationInsights",
            "credentials": {
                "instrumentationKey": APP_INSIGHTS_KEY
            }
        }
        apim_client.logger.create_or_update(
            resource_group_name=RESOURCE_GROUP,
            service_name=APIM_SERVICE_NAME,
            logger_id=logger_name,
            parameters=logger_params
        )
        logger.info(f"APIM Logger '{logger_name}' configured.")

        # 2. Set the Instrumentation Key as a Named Value for policies to use
        nv_params = NamedValueCreateContract(
            display_name=named_value_name,
            value=APP_INSIGHTS_KEY,
            secret=True # Mark it as a secret so it's not visible in the portal
        )
        apim_client.named_value.begin_create_or_update(
            resource_group_name=RESOURCE_GROUP,
            service_name=APIM_SERVICE_NAME,
            named_value_id=named_value_name,
            parameters=nv_params
        ).result()
        logger.info(f"APIM Named Value '{named_value_name}' configured.")

    except AzureError as e:
        logger.error(f"Failed to configure APIM observability backend: {e}")
        raise



def create_openid_connect_provider():
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

# Call this on operator startup
configure_apim_observability_backend()
create_openid_connect_provider()

# ### MODIFICATION START: New functions for observability ###

def patch_service_for_observability(service_name, component_name, namespace):
    """
    Patches the specified Service with standardized labels for observability.
    These labels are used for filtering in Azure Monitor and Grafana.
    """
    api = kubernetes.client.CoreV1Api()
    try:
        service = api.read_namespaced_service(name=service_name, namespace=namespace)
        
        labels = service.metadata.labels or {}
        original_labels = labels.copy()

        # Apply standardized labels
        labels['oda.tmforum.org/component'] = component_name
        labels['app.kubernetes.io/name'] = service_name
        labels['app.kubernetes.io/part-of'] = "oda-canvas"

        if labels != original_labels:
            body = {"metadata": {"labels": labels}}
            api.patch_namespaced_service(name=service_name, namespace=namespace, body=body)
            logger.info(f"Patched Service '{service_name}' in namespace '{namespace}' with observability labels.")
        else:
            logger.info(f"Service '{service_name}' already has required observability labels.")
            
        return service.spec.selector

    except ApiException as e:
        if e.status == 404:
            logger.warning(f"Service '{service_name}' not found in namespace '{namespace}' for observability patching.")
        else:
            logger.error(f"API Error patching Service '{service_name}': {e}")
            raise kopf.TemporaryError(f"Could not patch Service '{service_name}'.")
    return None

def patch_deployment_for_observability(selector, component_name, service_name, namespace, monitoring_spec):
    """
    Patches the Deployment corresponding to the service selector with standardized labels
    and Prometheus annotations for metric scraping by Azure Monitor Agent.
    """
    if not selector:
        logger.warning(f"No selector provided for service '{service_name}', cannot find and patch Deployment.")
        return

    api = kubernetes.client.AppsV1Api()
    selector_str = ",".join([f"{k}={v}" for k, v in selector.items()])
    
    try:
        deployments = api.list_namespaced_deployment(namespace=namespace, label_selector=selector_str)
        if not deployments.items:
            logger.warning(f"No deployment found with selector '{selector_str}' in namespace '{namespace}'.")
            return
            
        for deployment in deployments.items:
            dep_name = deployment.metadata.name
            
            # --- Patch Pod Template Metadata ---
            template_labels = deployment.spec.template.metadata.labels or {}
            template_annotations = deployment.spec.template.metadata.annotations or {}
            original_template_labels = template_labels.copy()
            original_template_annotations = template_annotations.copy()

            # Apply standardized labels to the pod template
            template_labels['oda.tmforum.org/component'] = component_name
            template_labels['app.kubernetes.io/name'] = service_name
            template_labels['app.kubernetes.io/part-of'] = "oda-canvas"

            # Apply Prometheus annotations for Azure Monitor Agent scraping
            if monitoring_spec and monitoring_spec.get('enabled', False):
                template_annotations['prometheus.io/scrape'] = "true"
                template_annotations['prometheus.io/port'] = str(monitoring_spec.get('port', 8080))
                template_annotations['prometheus.io/path'] = monitoring_spec.get('path', '/metrics')
            
            if template_labels != original_template_labels or template_annotations != original_template_annotations:
                body = {
                    "spec": {
                        "template": {
                            "metadata": {
                                "labels": template_labels,
                                "annotations": template_annotations
                            }
                        }
                    }
                }
                api.patch_namespaced_deployment(name=dep_name, namespace=namespace, body=body)
                logger.info(f"Patched Deployment '{dep_name}' Pod Template in '{namespace}' for observability.")
            else:
                logger.info(f"Deployment '{dep_name}' Pod Template already has required observability config.")

    except ApiException as e:
        logger.error(f"API Error patching Deployment with selector '{selector_str}': {e}")
        raise kopf.TemporaryError(f"Could not patch Deployment for service '{service_name}'.")

# ### MODIFICATION END ###

@kopf.on.create(GROUP, VERSION, APIS_PLURAL, retries=5)
@kopf.on.update(GROUP, VERSION, APIS_PLURAL, retries=5)
def manage_api_lifecycle(spec, name, namespace, status, meta, **kwargs):
    """
    Handles the creation and update events for the custom resource representing an API.
    This function manages the lifecycle by:
    - Creating or updating the Ingress resource to expose the service.
    - ### MODIFIED: Patching the component's Deployment/Service for observability. ###
    - Configuring the API in Azure API Management.
    - Applying policies such as JWT validation, rate limiting, and CORS.
    """
    # Extract API specifications
    api_spec = {
        "path": spec.get("path"),
        "name": name,
        "specification": spec.get("specification"),
        "implementation": spec.get("implementation"),
        "port": spec.get("port"),
        "rateLimit": spec.get("rateLimit", {}),
        "CORS": spec.get("CORS", {}),
        "monitoring": spec.get("monitoring", {}) # MODIFIED: Get monitoring spec
    }

    logger.info(f"Processing API resource '{name}' in namespace '{namespace}'.")

    if status and status.get('apimBind', {}).get('spec') == api_spec:
        logger.info(f"API '{name}' is already bound with the same spec. Skipping update.")
        return

    # ### MODIFICATION START: Trigger observability configuration ###
    implementation_service_name = api_spec.get("implementation")
    monitoring_spec = api_spec.get("monitoring")
    if implementation_service_name:
        logger.info(f"Configuring observability for component '{name}' backed by service '{implementation_service_name}'.")
        try:
            # First, patch the service to get its selector
            service_selector = patch_service_for_observability(
                service_name=implementation_service_name,
                component_name=name,
                namespace=namespace
            )
            # Then, use the selector to find and patch the corresponding deployment
            patch_deployment_for_observability(
                selector=service_selector,
                component_name=name,
                service_name=implementation_service_name,
                namespace=namespace,
                monitoring_spec=monitoring_spec
            )
        except Exception as e:
            # We raise a temporary error to retry, as this is a critical part of the setup
            logger.error(f"Failed to configure observability for '{name}': {e}")
            raise kopf.TemporaryError(f"Observability configuration failed for '{name}'. Retrying.")
    else:
        logger.warning(f"No 'implementation' service name specified for API '{name}'. Skipping observability patching.")
    # ### MODIFICATION END ###

    # Create or update the Ingress resource to expose the service
    ingress_created = create_or_update_ingress(spec, name, namespace, meta)
    if not ingress_created:
        logger.error("Ingress creation/update failed. Skipping APIM update.")
        # Do not proceed if ingress fails
        raise kopf.TemporaryError("Ingress creation failed, will retry.")

    # Update Azure API Management
    try:
        update_apim(api_spec, namespace)
        logger.info(f"API '{name}' successfully configured in Azure APIM.")
    except Exception as e:
        logger.error(f"Error updating Azure APIM for API '{name}': {e}")
        raise kopf.TemporaryError(f"Failed to configure API '{name}' in Azure APIM.")

    # Update the status of the custom resource
    try:
        api_client = kubernetes.client.CustomObjectsApi()
        api_obj = api_client.get_namespaced_custom_object(GROUP, VERSION, namespace, APIS_PLURAL, name)
        
        api_obj.setdefault('status', {})
        api_obj['status']['apimBind'] = {"spec": api_spec}
        api_obj['status']['implementation'] = {"ready": True}
        
        api_client.patch_namespaced_custom_object_status(GROUP, VERSION, namespace, APIS_PLURAL, name, {"status": api_obj['status']})
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
        ).result()
        
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
            poller = apim_client.api.begin_create_or_update( # Renamed to begin_...
                resource_group_name=RESOURCE_GROUP,
                service_name=APIM_SERVICE_NAME,
                api_id=api_name,
                parameters=api_parameters
            )
        else:
            # Update existing API with if_match
            poller = apim_client.api.begin_create_or_update( # Renamed to begin_...
                resource_group_name=RESOURCE_GROUP,
                service_name=APIM_SERVICE_NAME,
                api_id=api_name,
                parameters=api_parameters,
                if_match=etag
           )
               
        poller.result()
                
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
                
                <!-- E2E Observability: Start trace and correlate with backend -->
                <trace source="oda-api-gateway" correlation-id="{{context.RequestId}}">
                    <message>Request received for API: {api_id}, Path: {api_spec.get("path")}</message>
                    <metadata name="Ocp-Apim-Subscription-Key" value="{{context.Subscription?.Key}}"/>
                    <metadata name="Ocp-Apim-Trace" value="{{context.Trace.Id}}"/>
                </trace>

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