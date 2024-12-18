"""
Kubernetes Apisix API Lifecycle Management Operator for ODA API Custom Resources.

This module is part of the ODA Canvas, specifically tailored for environments adopting the Apisix API Gateway. It utilizes the Kopf Kubernetes operator framework (https://kopf.readthedocs.io/) to manage API custom resources. 
The operator is designed to seamlessly integrate with the Apisix API Gateway, facilitating the creation and management of ApisixRoute configurations to expose APIs.

Key Features:
- Automatically handles the lifecycle of ODA APIs including creation, update, and deletion of corresponding ApisixRoute resources to expose APIs through Apisix.
- Manages ApisixPluginConfig resources to apply and enforce various plugins and policies on APIs routed through Apisix.
- Configures an API gateway to act as a front aligning with recommended production architectures.

Usage:
This operator can be deployed as part of the ODA Canvas in Kubernetes clusters where the Apisix API Gateway is used to expose APIs. It simplifies the management of API exposure and security by interfacing directly with Apisix, 
providing a robust and scalable API management solution.
"""

import yaml
import kopf
import kubernetes.client
import logging
from kubernetes.client.rest import ApiException
import os
import requests

logging_level = os.environ.get("LOGGING", logging.INFO)
print("Logging set to ", logging_level)

kopf_logger = logging.getLogger()
kopf_logger.setLevel(logging.WARNING)

logger = logging.getLogger("APIOperator")
logger.setLevel(int(logging_level))


GROUP = "oda.tmforum.org"
VERSION = "v1"
APIS_PLURAL = "exposedapis"

group = "apisix.apache.org"  # API group for Gateway API
version = "v2"
plural = (
    "apisixroutes"  # The plural name of the Apisix route CRD - ApisixRoute resource
)


# try to recover from broken watchers https://github.com/nolar/kopf/issues/1036
@kopf.on.startup()
def configure(settings: kopf.OperatorSettings, **_):
    settings.watching.server_timeout = 1 * 60


@kopf.on.create(GROUP, VERSION, APIS_PLURAL, retries=5)
@kopf.on.update(GROUP, VERSION, APIS_PLURAL, retries=5)
def manage_api_lifecycle(spec, name, namespace, status, meta, logger, **kwargs):
    """
    Manages the lifecycle of an API by creating or updating the ApisixRoute, managing plugins, and handling error logging.

    Args:
    spec (dict): Contains the specification for the API lifecycle, including ingress configurations and plugin templates.
    name (str): The name of the API.
    namespace (str): The Kubernetes namespace where the API is deployed.
    status (str): The current status of the API lifecycle management.
    meta (dict): Metadata related to the API lifecycle management.
    logger (logging.Logger): Logger for logging messages about the process.
    kwargs: Arbitrary keyword arguments that may be used for additional configurations.

    Returns:
    None: This function does not return any value

    Description:
    - First, attempts to create or update an ApisixRoute based on the provided 'spec', 'name', 'namespace', and 'meta'.
    - If the ApisixRoute cannot be created or updated, it logs a failure message and the function returns early.
    - Checks if a template URL is provided in 'spec' and verifies its validity.
    - If valid, attempts to apply plugins based on the template. Logs the success or failure of this operation.
    - If plugins are successfully applied, updates the ApisixRoute with the plugin configuration.
    - Throughout the function, various informational and error logs are generated based on the operations performed.

    """

    Apisixroute_created = create_or_update_ingress(spec, name, namespace, meta)
    if not Apisixroute_created:
        logger.info(
            "ApisixRoute creation/update failed. Skipping plugin/policy management."
        )
        return

    template_url = spec.get("template", "")
    if template_url:
        if not check_url(template_url):
            logger.error(f"Invalid or inaccessible URL in template: {template_url}")

    applied_plugins = apply_plugins_from_template(namespace, name, spec, template_url)
    if applied_plugins:
        logger.info(f"Plugins applied: {applied_plugins}")
        patch_apisixroute_with_plugin_config(
            namespace, f"apisix-api-route-{name}", applied_plugins[0]
        )
    else:
        logger.error("Failed to apply plugins from template.")


def create_or_update_ingress(spec, name, namespace, meta, **kwargs):
    """
    Creates or updates an ApisixRoute ingress in a specified Kubernetes namespace based on the provided specifications.

    Args:
    spec (dict): Specifications for creating or updating the ingress, including the paths and backends.
    name (str): Name of the API for which the ingress is being managed.
    namespace (str): The initial namespace passed to the function.
    meta (dict): Metadata information used during the creation or update process.
    kwargs: Arbitrary keyword arguments for potential future use or custom extensions.

    Returns:
    bool: True if the ApisixRoute is successfully created or updated, False otherwise.

    Description:
    - Checks if the implementation status is 'ready'. If not, logs a message and skips ingress creation or update.
    - Constructs an ApisixRoute manifests using provided 'spec' details like path, backend service information.
    - Tries to find an existing ApisixRoute. If found, it updates the route using the existing 'resourceVersion'.
    - If no existing route is found and it's a case of a missing resource, it tries to create a new ApisixRoute and logs the outcome.
    - Catches and logs any API exceptions during the process, providing feedback on the success or failure of the operation.

    """

    # Check if 'implementation' is 'ready' this will be enabled once APIS_PLURAL = "exposedapis" will be used in components operator,reference examples not available as on 01 June 2024
    """
    if not status.get('implementation', {}).get('ready', False):
        logger.info(f"Implementation not ready for '{name}'. Ingress creation or update skipped.")
        return
    """

    api_instance = kubernetes.client.CustomObjectsApi()
    ingress_name = f"apisix-api-route-{name}"
    namespace = "istio-ingress"
    service_name = "istio-ingress"
    service_namespace = "istio-ingress"
    # strip_path = "false"
    service_port = 80

    try:
        path = spec.get(
            "path"
        )  # it will find if the path exists or not , will skip if no path
        if not path:
            logger.warning(f"Path not found  '{name}'. Apisixroute creation skipped.")
            return

            # Ensures the path matches the base and all subdirectories
        paths = [path, f"{path}/*"]  # Exact path  # Subpaths

        apisixroute_manifest = {
            "apiVersion": f"{group}/{version}",
            "kind": "ApisixRoute",
            "metadata": {
                "name": ingress_name,
                "namespace": namespace,
            },
            "spec": {
                "http": [
                    {
                        "name": "http-all",
                        "match": {"paths": paths},
                        "backends": [
                            {"serviceName": service_name, "servicePort": service_port}
                        ],
                    }
                ]
            },
        }
        # Kopf adoption is disabled as referencegrant is still pending for apisix api gateway. will enable adoption once this api gaetway feature enabled for apisix.
        # kopf.adopt(apisixroute_manifest)

        try:
            existing_route = api_instance.get_namespaced_custom_object(
                group=group,
                version=version,
                namespace=namespace,
                plural=plural,
                name=ingress_name,
            )
            resource_version = existing_route["metadata"]["resourceVersion"]
            apisixroute_manifest["metadata"]["resourceVersion"] = resource_version
            response = api_instance.replace_namespaced_custom_object(
                group=group,
                version=version,
                namespace=namespace,
                name=ingress_name,
                plural=plural,
                body=apisixroute_manifest,
            )
            logger.info(
                f"ApisixRoute '{ingress_name}' updated successfully in namespace '{namespace}'."
            )
            return True
        except ApiException as e:
            if e.status == 404:
                response = api_instance.create_namespaced_custom_object(
                    group=group,
                    version=version,
                    namespace=namespace,
                    plural=plural,
                    body=apisixroute_manifest,
                )
                logger.info(
                    f"ApisixRoute '{ingress_name}' created successfully in namespace '{namespace}'."
                )
                return True
            else:
                logger.error(f"API exception when accessing ApisixRoute: {e}")
                return False
    except ApiException as e:
        logger.error(f"Failed to create or update ApisixRoute '{ingress_name}': {e}")
        return False


def create_rate_limiting_policy(spec):
    """
    Constructs a rate limiting policy configuration from provided specifications.

    Args:
    spec (dict): Specifications containing the details of the rate limiting policy.

    Returns:
    dict or None: A dictionary representing the rate limiting policy if 'enabled' is True; otherwise, returns None.

    Description:
    - Extracts rate limiting configuration from the input specification.
    - If rate limiting is enabled, it configures a policy based on the specified limit and identifier.
    - Currently supports only per-second rate limiting. Ignores any interval settings and assumes rates are per second.
    - Constructs and returns a dictionary with the configuration for the rate limiting policy. The dictionary includes the rate, burst setting, key for identifying the rate limit scope, and whether to delay processing when under burst limit.
    - If rate limiting is not enabled, returns None.

    Note:
    - Default limit is set to 5 requests per second if not specified.
    - The default identifier is 'remote_addr'.
    """
    rate_limit_config = spec.get("rateLimit", {})
    if rate_limit_config.get("enabled", False):
        identifier = rate_limit_config.get("identifier", "remote_addr")
        limit = int(
            rate_limit_config.get("limit", "5")
        )  # Default to 5 if not specified

        # Logging a message about interval support provided by Apisix
        logger.info(
            "Note: Only per-second rate limiting is supported. Interval setting is ignored. Please be sure to pass rate in per second"
        )

        rate_limiting_policy = {
            "name": "limit-req",
            "enable": True,
            "config": {
                "rate": limit,
                "burst": 0,  # No extra burst
                "key": identifier,
                "nodelay": True,  # Process requests without delay if within burst limit
            },
        }
        return rate_limiting_policy
    else:
        return None


def create_quota_policy(spec):
    """
    Constructs a quota policy configuration from provided specifications.

    Args:
    spec (dict): Specifications containing the details of the quota policy.

    Returns:
    dict or None: A dictionary representing the quota policy if both 'identifier' and 'limit' are present and not empty; otherwise, returns None.

    Description:
    - Extracts quota configuration from the input specification.
    - Constructs a quota policy if both an identifier and a limit are defined in the specification.
    - Configures the policy with count limits, time window, identification key, and HTTP status code for rejection.
    - Constructs and returns a dictionary with the configuration for the quota policy. This includes count limits, time windows for the count, key for identifying the scope, and the rejection code.
    - Returns None if the necessary quota configuration is not completely defined.

    Note:
    - Default time window for the count limit is 60 seconds.
    - Default HTTP rejection code is 429.
    """
    # if quota_config.get('enabled', False):    this check condition need to be updated in exposedapis crd and enabled as primary condition for quota in CR after that.
    quota_config = spec.get("quota", {})
    identifier = quota_config.get("identifier")
    limit = quota_config.get("limit")

    if identifier and limit:
        try:
            count = int(limit)  # Convert the limit from string to integer
        except ValueError:
            logger.error(f"Invalid limit value provided for quota policy: {limit}")
            return None

        time_window = 60  # Default time window to 60 seconds if not specified
        rejected_code = 429  # Default for HTTP status code on rejection

        quota_policy = {
            "name": "limit-count",
            "enable": True,
            "config": {
                "count": count,
                "time_window": time_window,
                "key": identifier,
                "rejected_code": rejected_code,
            },
        }
        return quota_policy
    else:
        # Either 'identifier' or 'limit' was not provided, or they were empty
        return None


def create_oas_validation_policy(spec):
    """
    Constructs an OpenAPI Specification (OAS) validation policy configuration based on the provided specifications.

    Args:
    spec (dict): Specifications containing the details for the OAS validation policy.

    Returns:
    dict or None: A dictionary representing the OAS validation policy if either request or response validation is enabled; otherwise, returns None.

    Description:
    - Extracts the OAS validation configuration from the input specification.
    - Checks if either request or response validation is explicitly enabled.
    - If either validation is enabled, prints a notice about the availability of the OAS validation policy only through API7, a commercial extension of APISIX, and does not create the policy. Refer to the official documentation for more information.
    - If the policy were to be created, it would be configured with settings for validating requests and responses, along with allowances for unspecified headers, query parameters, and cookies.
    - Returns None as the creation of the policy is not supported outside of API7, as per the function's current implementation.

    Note:
    - The function currently acts to inform about the commercial availability of the feature in enterprise version and does not return a policy configuration.
    """
    oas_validation_config = spec.get("OASValidation", {})
    request_enabled = oas_validation_config.get("requestEnabled", False)
    response_enabled = oas_validation_config.get("responseEnabled", False)

    # Creating the policy only if either is true
    if request_enabled or response_enabled:
        logger.error(
            "Note: This policy will not be created as oas-validator plugin is available through API7 only, a commercial extension of APISIX. Check - https://docs.api7.ai/hub/oas-validator"
        )
        """
        oas_validation_policy = {
            'name': 'oas-validation',
            'enable': True,
            'config': {
                'requestValidation': request_enabled,
                'responseValidation': response_enabled,
                'allowUnspecifiedHeaders': oas_validation_config.get('allowUnspecifiedHeaders', False),
                'allowUnspecifiedQueryParams': oas_validation_config.get('allowUnspecifiedQueryParams', False),
                'allowUnspecifiedCookies': oas_validation_config.get('allowUnspecifiedCookies', False)
            }
        }

        return oas_validation_policy
        """
    return None


def create_cors_policy(spec):
    """
    Constructs a Cross-Origin Resource Sharing (CORS) policy configuration based on the provided specifications.

    Args:
    spec (dict): Specifications containing the details for the CORS policy.

    Returns:
    dict or None: A dictionary representing the CORS policy if enabled; otherwise, returns None.

    Description:
    - Extracts CORS configuration from the input specification.
    - Constructs a CORS policy if CORS is enabled in the specification. This policy includes configurations such as allowed origins, credentials, and preflight request handling.
    - The preflight request handling includes settings for allowed methods, headers, and the maximum age for caching preflight responses.
    - Returns a dictionary with the complete configuration for the CORS policy.
    - If CORS is not enabled in the specification, returns None.

    Note:
    - Default settings include allowing all origins, a standard set of headers and methods for preflight requests, and a default max age of 3600 seconds for preflight caching.
    """
    cors_config = spec.get("CORS", {})
    if cors_config.get("enabled", False):
        preflight_config = cors_config.get("handlePreflightRequests", {})

        cors_policy = {
            "name": "cors",
            "enable": True,
            "config": {
                "allowCredentials": cors_config.get("allowCredentials", False),
                "allowOrigins": cors_config.get("allowOrigins", "*").split(","),
                "handlePreflightRequests": {
                    "enabled": preflight_config.get("enabled", False),
                    "allowHeaders": preflight_config.get(
                        "allowHeaders",
                        "Accept, X-Requested-With, Content-Type, Access-Control-Request-Method, Access-Control-Request-Headers",
                    ),
                    "allowMethods": preflight_config.get("allowMethods", "GET, POST"),
                    "maxAge": int(preflight_config.get("maxAge", 3600)),
                },
            },
        }
        return cors_policy
    return None


def create_api_key_verification_policy(spec):
    """
    Constructs an API key verification policy configuration based on the provided specifications.

    Args:
    spec (dict): Specifications containing the details for the API key verification policy.

    Returns:
    dict or None: A dictionary representing the API key verification policy if enabled; otherwise, returns None.

    Description:
    - Extracts API key verification configuration from the input specification.
    - Constructs an API key verification policy if API key verification is enabled in the specification.
    - Returns a dictionary with the configuration for the API key verification policy.
    - If API key verification is not enabled in the specification, returns None.

    Note:
    - The 'location' field specifies where the API key is expected to be found in the request, typically in headers.
    """
    api_key_config = spec.get("apiKeyVerification", {})
    if api_key_config.get("enabled", False):
        api_key_policy = {
            "name": "key-auth",
            "enable": True,
            "config": {"key": api_key_config.get("location")},
        }
        return api_key_policy
    return None


def check_url(url):
    """
    Checks the accessibility of a URL by making a HEAD request.

    Args:
    url (str): The URL to be checked.

    Returns:
    bool: True if the URL is accessible, False if any error occurs.

    Description:
    - Attempts to make a HEAD request to the specified URL to check its accessibility.
    - Raises an HTTP error if the request returns an unsuccessful status code, indicating that the URL is not reachable or valid.
    - If an exception occurs during the request, logs an error message detailing the issue and returns False.

    Note:
    - This function is used to validate URLs in scenarios where URLs are required for further processing, such as downloading content or validating links in configurations.
    """
    try:
        response = requests.head(url)
        response.raise_for_status()  # This Raising HTTPError if the HTTP request returned an unsuccessful
        return True
    except requests.RequestException as e:
        logger.error(f"Failed to reach the given URL in CR template: {url}. Error: {e}")
        return False


def download_and_append_plugin_names(url, plugin_names):
    """
    Downloads plugin configurations from a specified URL and appends their names to a provided list.

    Args:
    url (str): The URL from where to download the plugin configurations.
    plugin_names (list): A list of plugin names to which new names will be appended.

    Returns:
    tuple: A tuple containing the updated list of plugin names and the downloaded plugins, or (None, None) if an error occurs.

    Description:
    - Makes a request to the specified URL with caching disabled to download plugin configurations.
    - Parses the response as YAML to extract plugin details.
    - Appends the names of the plugins to the provided list and prints the updated list and the combined plugin details.
    - Returns the updated list of plugin names and the list of plugins.
    - If an error occurs during the download or parsing, logs an error and returns (None, None).

    Note:
    - This function is useful for dynamically configuring API gateways by downloading and integrating external plugin configurations.
    """
    try:
        headers = {"Cache-Control": "no-cache", "Pragma": "no-cache"}
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        content = yaml.safe_load(response.text)
        plugins = content.get("spec", {}).get("plugins", [])

        for plugin in plugins:
            if "name" in plugin:
                plugin_names.append(plugin["name"])

        return plugin_names, plugins
    except requests.RequestException as e:
        logger.error(
            f"Failed to download or parse the ApisixPluginConfig from URL: {url}. Error: {e}"
        )
        return None, None


def combine_all_policies_with_plugins(spec, plugin_names, plugins):
    """
    Combines API management policies created from specifications with existing plugin configurations.

    Args:
    spec (dict): Specifications that may include settings for various API management policies.
    plugin_names (list): A list of plugin names initially provided or derived from another part of the system.
    plugins (list): A list of existing plugin configurations.

    Returns:
    tuple: A tuple containing two lists: updated plugin names and their corresponding plugin configurations.

    Description:
    - Initializes lists to collect names and configurations of plugins derived from custom resource definitions (CRDs).
    - Iterates over a list of policy creator functions, each designed to generate a specific type of API management policy from the given specifications.
    - For each policy, if it is successfully created, adds its name to the list of plugin names and its configuration to the list of plugins.
    - Combines these newly created policy configurations with any existing plugin names and configurations.
    - Returns the combined lists of plugin names and configurations, reflecting an integrated set of API management tools.

    Note:
    - The function leverages policy creators for rate limiting, quota management, OAS validation, CORS, and API key verification.
    - This function is crucial for dynamically constructing a comprehensive set of API management plugins based on both static configuration and dynamic specifications.
    """
    plugin_names_from_crd = []
    plugins_from_crd = []

    policy_creators = [
        create_rate_limiting_policy,
        create_quota_policy,
        create_oas_validation_policy,
        create_cors_policy,
        create_api_key_verification_policy,
    ]

    for creator in policy_creators:
        policy = creator(spec)
        if policy:
            plugin_names_from_crd.append(policy["name"])
            plugins_from_crd.append(policy)

    # Combine CRD derived plugins with those potentially derived from the template
    plugin_names += plugin_names_from_crd
    plugins += plugins_from_crd

    # added this print plugins in more clearly visible manner
    plugins_complete_yaml = yaml.dump(plugins, sort_keys=False)
    plugins_name_yaml = yaml.dump(plugin_names, sort_keys=False)
    logger.info(
        "Combined plugins from CR and Template URL.\nUpdated Plugin Names List:\n"
        + str(plugins_name_yaml)
        + "\nComplete details are as below:\n"
        + str(plugins_complete_yaml)
    )
    return plugin_names, plugins


def apply_plugins_from_template(namespace, api_name, spec, url):
    """
    Applies plugin configurations to an API from a specified template URL and CRD-based policies.

    Args:
    namespace (str): The Kubernetes namespace where the plugin configurations will be applied.
    api_name (str): The name of the API to which the plugins are being applied.
    spec (dict): Specifications for creating policy-based plugins.
    url (str, optional): The URL from which to download additional plugin configurations.

    Returns:
    list or None: A list containing the name of the modified plugin configuration if successful, None otherwise.

    Description:
    - Initializes empty lists for plugin names and plugins.
    - If a URL is provided, downloads and appends additional plugin configurations.
    - Combines these plugins with CRD-based policies using the `combine_all_policies_with_plugins` function.
    - Constructs an `ApisixPluginConfig` Kubernetes custom object and attempts to either create or update it in the specified namespace.
    - Handles Kubernetes API exceptions by logging errors and providing feedback on the success or failure of the operation.

    Note:
    - This function is critical for deploying combined plugin configurations to APIs, facilitating dynamic API gateway management.
    """
    plugin_names = []
    plugins = []
    namespace = "istio-ingress"

    if url:
        plugin_names, plugins = download_and_append_plugin_names(url, plugin_names)

    # Combines CRD-based policies with those downloaded from the templatex
    plugin_names, plugins = combine_all_policies_with_plugins(
        spec, plugin_names, plugins
    )

    modified_name = f"combined-apisixpluginconfig-{api_name}"
    if plugins:
        plugin_config = {
            "apiVersion": "apisix.apache.org/v2",
            "kind": "ApisixPluginConfig",
            "metadata": {"name": modified_name, "namespace": namespace},
            "spec": {"plugins": plugins},
        }
    else:
        plugin_config = {
            "apiVersion": "apisix.apache.org/v2",
            "kind": "ApisixPluginConfig",
            "metadata": {"name": modified_name, "namespace": namespace},
        }
        logger.warning("No plugins found; applying plugin config with an empty 'spec'.")

    # kopf.adopt(plugin_config)Kopf adoption is disabled as referencegrant is still pending for apisix api gateway. will enable adoption once this api gaetway feature enabled for apisix.
    api_instance = kubernetes.client.CustomObjectsApi()
    group, version = plugin_config["apiVersion"].split("/")
    plural = "apisixpluginconfigs"

    try:
        existing_plugin = api_instance.get_namespaced_custom_object(
            group, version, namespace, plural, name=modified_name
        )
        resource_version = existing_plugin["metadata"]["resourceVersion"]
        plugin_config["metadata"]["resourceVersion"] = resource_version
        api_instance.replace_namespaced_custom_object(
            group, version, namespace, plural, name=modified_name, body=plugin_config
        )
        logger.info(
            f"Plugin config '{modified_name}' updated successfully in namespace '{namespace}'."
        )
        return [modified_name]
    except kubernetes.client.exceptions.ApiException as e:
        if e.status == 404:
            api_instance.create_namespaced_custom_object(
                group, version, namespace, plural, body=plugin_config
            )
            logger.info(
                f"Plugin config '{modified_name}' created successfully in namespace '{namespace}'."
            )
            return [modified_name]
        else:
            logger.error(f"Failed to apply plugin config '{modified_name}': {e}")
            return None


def patch_apisixroute_with_plugin_config(
    namespace, apisixroute_name, plugin_config_name
):
    """
    Updates an existing ApisixRoute to include a specific plugin configuration.

    Args:
    namespace (str): The Kubernetes namespace where the ApisixRoute is located.
    apisixroute_name (str): The name of the ApisixRoute to be patched.
    plugin_config_name (str): The name of the plugin configuration to apply to the ApisixRoute.

    Returns:
    None: This function does not return a value but logs the outcome of the operation.

    Description:
    - Connects to the Kubernetes API and attempts to fetch the existing ApisixRoute specified by `apisixroute_name`.
    - If the route is successfully retrieved, it updates the 'plugin_config_name' within the 'http' blocks of the route's specification.
    - Applies the updated configuration using a strategic merge patch to the existing ApisixRoute.
    - Logs informational messages regarding the successful patching of the route, or error messages if any part of the process fails.

    Note:
    - Uses error handling to manage and log exceptions related to fetching or patching the ApisixRoute, ensuring that all potential issues are reported.
    - The strategic merge patch method is used to ensure that changes are applied correctly without replacing the entire route configuration.
    """
    api_instance = kubernetes.client.CustomObjectsApi()
    group = "apisix.apache.org"
    version = "v2"
    plural = "apisixroutes"
    namespace = "istio-ingress"

    # Fetching the existing configuration first
    try:
        existing_route = api_instance.get_namespaced_custom_object(
            group=group,
            version=version,
            namespace=namespace,
            plural=plural,
            name=apisixroute_name,
        )
    except ApiException as e:
        logger.error(f"Failed to get ApisixRoute '{apisixroute_name}': {e}")
        return

    # Updating the plugin_config_name in the existing http block
    try:
        if "http" in existing_route["spec"]:
            for http_block in existing_route["spec"]["http"]:
                http_block["plugin_config_name"] = plugin_config_name
    except KeyError as e:
        logger.error(f"Key error while updating the plugin_config_name: {e}")
        return

    # Using patch_namespaced_custom_object to apply a strategic merge patch
    try:
        api_instance.patch_namespaced_custom_object(
            group=group,
            version=version,
            namespace=namespace,
            plural=plural,
            name=apisixroute_name,
            body=existing_route,
        )
        logger.info(
            f"ApisixRoute '{apisixroute_name}' patched with plugin config '{plugin_config_name}' in namespace '{namespace}'."
        )
    except ApiException as e:
        logger.error(
            f"Failed to patch ApisixRoute '{apisixroute_name}' with plugin config '{plugin_config_name}': {e}"
        )


@kopf.on.delete(GROUP, VERSION, APIS_PLURAL, retries=1)
def delete_api_lifecycle(meta, name, namespace, **kwargs):
    """
    Deletes API lifecycle resources, including ApisixRoutes and ApisixPluginConfigs, for a specified API in a Kubernetes namespace.

    Args:
    meta (dict): Metadata associated with the API lifecycle resources.
    name (str): The name of the API whose lifecycle resources are to be deleted.
    namespace (str): The Kubernetes namespace where the resources are located. Though provided, not directly used due to predefined 'istio-ingress'.
    kwargs: Arbitrary keyword arguments that can be used for additional configurations or extensions.

    Returns:
    None: This function does not return a value but logs the outcome of the deletion operations.

    Description:
    - Logs the initiation of the deletion process for the API.
    - Defines the names of the resources associated with the API (ApisixRoute and ApisixPluginConfig) using a naming convention based on the API's name.
    - Attempts to delete the ApisixRoute and ApisixPluginConfig from the 'istio-ingress' namespace.
    - Handles exceptions related to Kubernetes API interactions, logging errors if deletions fail.

    Note:
    - Once referencegrant feature becomes available than this deletion function will be removed as it will be automatically handled using kopf.adopt and garbage collection
    - All deletions are attempted within the 'istio-ingress' namespace, regardless of the 'namespace' argument provided, reflecting a typical use case in an Istio-managed environment.
    - The function uses the 'apisix.apache.org' group and 'v2' version for Kubernetes custom objects, which are common in APISIX integrations.
    - This function is vital for cleaning up resources when an API is decommissioned or when its lifecycle management needs to be reset.
    """
    logger.info(f"ExposedAPI '{name}' deleted from namespace '{namespace}'.")

    # Defining the names of the resources to delete
    apisix_route_name = f"apisix-api-route-{name}"
    apisix_plugin_name = f"combined-apisixpluginconfig-{name}"
    apisix_plugin_namespace = "istio-ingress"
    apisixroute_namespace = "istio-ingress"
    group = "apisix.apache.org"
    version = "v2"
    plural_ar = "apisixroutes"
    plural_apc = "apisixpluginconfigs"

    api_instance = kubernetes.client.CustomObjectsApi()

    # Deleting the ApisixRoute
    try:
        api_instance.delete_namespaced_custom_object(
            group=group,
            version=version,
            namespace=apisixroute_namespace,
            plural=plural_ar,
            name=apisix_route_name,
        )
        logger.info(
            f"ApisixRoute '{apisix_route_name}' deleted successfully from namespace '{namespace}'."
        )
    except ApiException as e:
        logger.error(f"Failed to delete ApisixRoute '{apisix_route_name}': {e}")

    # Deleting the ApisixPluginConfig
    try:
        api_instance.delete_namespaced_custom_object(
            group=group,
            version=version,
            namespace=apisixroute_namespace,
            plural=plural_apc,
            name=apisix_plugin_name,
        )
        logger.info(
            f"ApisixPluginConfig '{apisix_plugin_name}' deleted successfully from namespace '{apisix_plugin_namespace}'."
        )
    except ApiException as e:
        logger.error(f"Failed to delete ApisixPluginConfig '{apisix_plugin_name}': {e}")
