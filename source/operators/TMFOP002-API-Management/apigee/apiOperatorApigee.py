import kopf
import os
import json
import requests
import zipfile

from kubernetes import client, config
from kubernetes.client.exceptions import ApiException

import google.auth
import google.auth.transport.requests
from google.oauth2 import service_account

from base_logger import logger
from apigee_utils import Apigee
from utils.apiproxy_utils import generate_apiproxy_files

APIGEE_ORG = os.environ.get("APIGEE_ORG")
APIGEE_ENV = os.environ.get("APIGEE_ENV")

GROUP = "oda.tmforum.org"
VERSION = "v1"
APIS_PLURAL = "exposedapis"

def get_istio_ingress_external():
    #Returns the external IP or hostname for the Istio ingressgateway service , check with team later if any other method required
    try:
        # Load in-cluster config ,make if only in cluster after proper helm chart
        try:
            config.load_incluster_config()
        except:
            config.load_kube_config()

        v1 = client.CoreV1Api()
        label_selector = "istio=ingressgateway"
        svc_list = v1.list_service_for_all_namespaces(label_selector=label_selector)

        if not svc_list.items:
            return ""

        svc = svc_list.items[0]
        lb_ingress = svc.status.load_balancer and svc.status.load_balancer.ingress or []
        if lb_ingress:
            ip = lb_ingress[0].ip
            hostname = lb_ingress[0].hostname
            return ip if ip else (hostname if hostname else "")
    except ApiException as e:
        logger.error(f"Failed to discover Istio ingress IP: {e}")

    return ""

BUNDLE_PATH = os.path.dirname(os.path.abspath(__file__))

# Initialize Apigee client
apigee = Apigee(
    apigee_type="x",
    org=APIGEE_ORG
)

@kopf.on.create(GROUP, VERSION, APIS_PLURAL, retries=5)
def create_exposedapi_handler(body, **kwargs):
    logger.info("ExposedAPI created")

    # 1) Extract core properties from CR
    API_NAME = body['metadata']['name']
    UNIQUE_ID = body['metadata']['uid']
    RESOURCE_VERSION = body['metadata']['resourceVersion']
    
    # 2) Discover the external IP or hostname
    external_ip = get_istio_ingress_external()
    if not external_ip:
        raise kopf.TemporaryError("No external IP found for Istio ingressgateway service.")

    # 3) Construct TARGET_URL from the discovered IP
    TARGET_URL = f"https://{external_ip}/"
    #logger.info(f"Using istio-ingress {TARGET_URL} as the target URL.")
    BASE_PATH = body['spec']['path']
    
    # Read the template field (if any) from the CR.
    TEMPLATE = body['spec'].get('template', "").strip()
    
    STAGING_DIR = f"{UNIQUE_ID}-{RESOURCE_VERSION}"
    staging_path = os.path.join(BUNDLE_PATH, "generated", STAGING_DIR)

    # 2) Determine if SpikeArrest is required
    SPIKE_ARREST_REQUIRED = body['spec']['rateLimit']['enabled']
    SPIKE_ARREST_IDENTIFIER = ""
    SPIKE_ARREST_RATE = ""
    SPIKE_ARREST_STEP = ""
    
    if SPIKE_ARREST_REQUIRED:
        logger.info(f"SpikeArrest policy is enabled for {API_NAME}.")
        SPIKE_ARREST_IDENTIFIER = body['spec']['rateLimit']['identifier']
        limit = body['spec']['rateLimit']['limit']
        interval = body['spec']['rateLimit']['interval']
        SPIKE_ARREST_RATE = f"{limit}{interval}"
        SPIKE_ARREST_STEP = "<Step><Name>SpikeArrest.RateLimit</Name></Step>"
    else:
        logger.info(f"SpikeArrest policy NOT enabled for {API_NAME}.")

    # 3) Determine if VerifyAPIKey is required
    VERIFY_API_KEY_REQUIRED = body['spec']['apiKeyVerification']['enabled']
    API_KEY_LOCATION = ""
    VERIFY_API_KEY_STEP = ""
    
    if VERIFY_API_KEY_REQUIRED:
        logger.info(f"VerifyAPIKey policy is enabled for {API_NAME}.")
        API_KEY_LOCATION = body['spec']['apiKeyVerification']['location']
        VERIFY_API_KEY_STEP = "<Step><Name>VerifyAPIKey.Validate</Name></Step>"
    else:
        logger.info(f"VerifyAPIKey policy NOT enabled for {API_NAME}.")

    # 4) Determine if CORS is enabled.
    cors = body['spec'].get('CORS', {})
    cors_enabled = cors.get('enabled', False)
    if cors_enabled:
        cors_allowCredentials = cors.get('allowCredentials', False)
        cors_allowOrigins = cors.get('allowOrigins', '*')
        cors_handlePreflight = cors.get('handlePreflightRequests', {})
        cors_handlePreflightEnabled = cors_handlePreflight.get('enabled', True)
        cors_handlePreflightAllowHeaders = cors_handlePreflight.get('allowHeaders', 'Origin, Accept, X-Requested-With, Content-Type, Access-Control-Request-Method, Access-Control-Request-Headers')
        cors_handlePreflightAllowMethods = cors_handlePreflight.get('allowMethods', 'GET, POST, HEAD, OPTIONS')
        cors_handlePreflightMaxAge = cors_handlePreflight.get('maxAge', 1800)
        logger.info(f"CORS policy is enabled for {API_NAME}.")
    else:
        cors_enabled = False
        cors_allowCredentials = False
        cors_allowOrigins = ""
        cors_handlePreflightEnabled = False
        cors_handlePreflightAllowHeaders = ""
        cors_handlePreflightAllowMethods = ""
        cors_handlePreflightMaxAge = 0
        logger.info(f"CORS policy is not enabled for {API_NAME}.")

    # 5) Generate the apiproxy/ directory from inline templates.
    logger.info(f"Generating apiproxy files for {API_NAME} at {staging_path}...")
    generate_apiproxy_files(
        bundle_path=staging_path,
        name=API_NAME,
        identifier=SPIKE_ARREST_IDENTIFIER,
        rate=SPIKE_ARREST_RATE,
        location=API_KEY_LOCATION,
        spike_arrest_step=SPIKE_ARREST_STEP,
        verify_api_key_step=VERIFY_API_KEY_STEP,
        base_path=BASE_PATH,
        target_url=TARGET_URL,
        cors_enabled=cors_enabled,
        cors_allowCredentials=cors_allowCredentials,
        cors_allowOrigins=cors_allowOrigins,
        cors_handlePreflightEnabled=cors_handlePreflightEnabled,
        cors_handlePreflightAllowHeaders=cors_handlePreflightAllowHeaders,
        cors_handlePreflightAllowMethods=cors_handlePreflightAllowMethods,
        cors_handlePreflightMaxAge=cors_handlePreflightMaxAge,
        template_name=TEMPLATE
    )

    # 6) Zip up the newly created directory 
    def zipdir(path, ziph):
        for root, _, files in os.walk(path):
            for file in files:
                ziph.write(
                    os.path.join(root, file),
                    os.path.relpath(os.path.join(root, file), os.path.join(path, ".."))
                )

    def create_proxy_bundle(proxy_bundle_directory, api_name, target_dir):
        zip_file_path = os.path.join(proxy_bundle_directory, f"{api_name}.zip")
        with zipfile.ZipFile(zip_file_path, "w", zipfile.ZIP_DEFLATED) as zipf:
            zipdir(target_dir, zipf)
        return zip_file_path

    logger.info(f"Creating proxy bundle zip for {API_NAME} ({STAGING_DIR})...")
    proxy_bundle_zip = create_proxy_bundle(
        proxy_bundle_directory=staging_path, 
        api_name=API_NAME,
        target_dir=os.path.join(staging_path, "apiproxy")
    )

    # 7) Deploy the proxy bundle to Apigee
    logger.info(f"Deploying {proxy_bundle_zip} to Apigee environment: {APIGEE_ENV}...")
    if not apigee.deploy_api_bundle(APIGEE_ENV, API_NAME, proxy_bundle_zip, True):
        logger.error(f"Deployment failed for {API_NAME} ({STAGING_DIR})")
    else:
        logger.info(f"Deployment succeeded for {API_NAME} ({STAGING_DIR})")

@kopf.on.delete(GROUP, VERSION, APIS_PLURAL, retries=5)
def delete_exposedapi_handler(body, **kwargs):
    API_NAME = body['metadata']['name']
    logger.info("Deletion requested for ExposedAPI %s", API_NAME)
    if apigee.delete_api(API_NAME):
        logger.info("Proxy %s deleted successfully.", API_NAME)
    else:
        logger.error("Failed to delete proxy %s.", API_NAME)

if __name__ == '__main__':
    kopf.run()
