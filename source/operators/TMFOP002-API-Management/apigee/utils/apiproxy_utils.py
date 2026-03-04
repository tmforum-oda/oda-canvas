import os
from jinja2 import Template
from base_logger import logger
import requests
import tempfile
import xml.etree.ElementTree as ET

APIPROXY_TEMPLATES = {
    # 1) apiproxy.xml
    "apiproxy/apiproxy.xml": """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<APIProxy revision="1" name="{{ name }}"/>""",
    
    # 2) policies/SpikeArrest.RateLimit.xml
    "apiproxy/policies/SpikeArrest.RateLimit.xml": """<SpikeArrest continueOnError="false" enabled="true" name="SpikeArrest.RateLimit">
    <Identifier ref="{{ identifier }}" />
    <Rate>{{ rate }}</Rate>
    <UseEffectiveCount>true</UseEffectiveCount>
</SpikeArrest>""",
    
    # 3) policies/VerifyAPIKey.Validate.xml
    "apiproxy/policies/VerifyAPIKey.Validate.xml": """<VerifyAPIKey continueOnError="false" enabled="true" name="VerifyAPIKey.Validate">
    <APIKey ref="{{ location }}" />
</VerifyAPIKey>""",
    
    # 4) policies/CORS.xml
    "apiproxy/policies/CORS.xml": """<CORS enabled="{{ cors_enabled }}" name="CORS">
    <AllowOrigins>{{ cors_allowOrigins }}</AllowOrigins>
    <AllowCredentials>{{ cors_allowCredentials }}</AllowCredentials>
    <HandlePreflightRequests enabled="{{ cors_handlePreflightEnabled }}">
       <AllowHeaders>{{ cors_handlePreflightAllowHeaders }}</AllowHeaders>
       <AllowMethods>{{ cors_handlePreflightAllowMethods }}</AllowMethods>
       <MaxAge>{{ cors_handlePreflightMaxAge }}</MaxAge>
    </HandlePreflightRequests>
</CORS>""",
    
    # 5) proxies/default.xml (added template for remote policy step)
    "apiproxy/proxies/default.xml": """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<ProxyEndpoint name="default">
  <PreFlow name="PreFlow">
    <Request>
        {{ spike_arrest_step }}
        {{ verify_api_key_step }}
        {{ cors_step }}
        {{ remote_policy_step }}
    </Request>
    <Response/>
  </PreFlow>
  <Flows/>
  <PostFlow name="PostFlow">
    <Request/>
    <Response/>
  </PostFlow>
  <HTTPProxyConnection>
    <BasePath>{{ base_path }}</BasePath>
  </HTTPProxyConnection>
  <RouteRule name="default">
    <TargetEndpoint>default</TargetEndpoint>
  </RouteRule>
</ProxyEndpoint>""",
    
    # 6) targets/default.xml
    "apiproxy/targets/default.xml": """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<TargetEndpoint name="default">
  <PreFlow name="PreFlow">
    <Request/>
    <Response/>
  </PreFlow>
  <Flows/>
  <PostFlow name="PostFlow">
    <Request/>
    <Response/>
  </PostFlow>
  <HTTPTargetConnection>
    <URL>{{ target_url }}</URL>
  </HTTPTargetConnection>
</TargetEndpoint>"""
}

def generate_apiproxy_files(
    bundle_path,
    name,
    identifier,
    rate,
    location,
    spike_arrest_step,
    verify_api_key_step,
    base_path,
    target_url,
    cors_enabled=False,
    cors_allowCredentials=False,
    cors_allowOrigins="",
    cors_handlePreflightEnabled=False,
    cors_handlePreflightAllowHeaders="",
    cors_handlePreflightAllowMethods="",
    cors_handlePreflightMaxAge=0,
    template_name=""
):
    from base_logger import logger
    from jinja2 import Template

    # Ensure target_url has a proper scheme type.
    if target_url and not target_url.startswith(('http://', 'https://', 'ws://', 'wss://')):
        logger.warning("Target URL '%s' does not start with a valid scheme. Prepending 'http://'.", target_url)
        target_url = "http://" + target_url

    if not os.path.exists(bundle_path):
        os.makedirs(bundle_path, exist_ok=True)
    
    # Additional policy step for handling CORS
    cors_step = "<Step><Name>CORS</Name></Step>" if cors_enabled else ""
    
    # Preparing remote policy step and file if a template having some URL.
    remote_policy_step = ""
    if template_name:
        if template_name.startswith("http://") or template_name.startswith("https://"):
            logger.info("Downloading remote template from %s", template_name)
            try:
                response = requests.get(template_name)
                response.raise_for_status()
                template_content = response.text
                # Parse the XML to get the element name from template file. Need to update later to handle multiple policy together later.
                root = ET.fromstring(template_content)
                policy_root_name = root.tag  
                remote_policy_file = os.path.join(bundle_path, "apiproxy", "policies", f"{policy_root_name}.xml")
                os.makedirs(os.path.dirname(remote_policy_file), exist_ok=True)
                with open(remote_policy_file, "w") as f:
                    f.write(template_content)
                # Adding  the step to reference the policy by its element name.
                remote_policy_step = f"<Step><Name>{policy_root_name}</Name></Step>"
                logger.info("Remote policy '%s' saved to %s", policy_root_name, remote_policy_file)
            except Exception as e:
                logger.error("Failed to download or parse remote template from %s: %s", template_name, e)
        else:
            # Assume local templates are stored in "templates/something" >. This need testing.
            template_dir = os.path.join(os.path.dirname(__file__), "templates", template_name)
            if os.path.exists(template_dir):
                logger.info("Applying additional local template '%s' from %s", template_name, template_dir)
                parts = []
                for root, dirs, files in os.walk(template_dir):
                    for file in sorted(files):
                        file_path = os.path.join(root, file)
                        with open(file_path, "r") as f:
                            parts.append(f.read())
                template_content = "\n".join(parts)
                # Parse local content to extract element name.
                try:
                    root_elem = ET.fromstring(template_content)
                    policy_root_name = root_elem.tag
                except Exception as e:
                    logger.error("Failed to parse local template content: %s", e)
                    policy_root_name = "RemotePolicy"
                # Save as a separate policy file.
                remote_policy_file = os.path.join(bundle_path, "apiproxy", "policies", f"{policy_root_name}.xml")
                os.makedirs(os.path.dirname(remote_policy_file), exist_ok=True)
                with open(remote_policy_file, "w") as f:
                    f.write(template_content)
                remote_policy_step = f"<Step><Name>{policy_root_name}</Name></Step>"
            else:
                logger.error("Template directory %s does not exist.", template_dir)

    # Building the rendering context
    context = {
        "name": name,
        "identifier": identifier,
        "rate": rate,
        "location": location,
        "spike_arrest_step": spike_arrest_step,
        "verify_api_key_step": verify_api_key_step,
        "base_path": base_path,
        "target_url": target_url,
        "cors_enabled": cors_enabled,
        "cors_allowCredentials": cors_allowCredentials,
        "cors_allowOrigins": cors_allowOrigins,
        "cors_handlePreflightEnabled": cors_handlePreflightEnabled,
        "cors_handlePreflightAllowHeaders": cors_handlePreflightAllowHeaders,
        "cors_handlePreflightAllowMethods": cors_handlePreflightAllowMethods,
        "cors_handlePreflightMaxAge": cors_handlePreflightMaxAge,
        "cors_step": cors_step,
        "template_name": template_name,
        "remote_policy_step": remote_policy_step
    }

    for relative_path, template_str in APIPROXY_TEMPLATES.items():
        # Skipping policy files if the corresponding configuration is not provided. CR need to be updated for Quota and OAS validation as some fields which APIGEE require are missing in CRD. Check later with Google team.
        if "VerifyAPIKey.Validate.xml" in relative_path and (not verify_api_key_step or not location):
            logger.info("Skipping generation of VerifyAPIKey policy file because API key verification is disabled or location is empty.")
            continue
        if "SpikeArrest.RateLimit.xml" in relative_path and not spike_arrest_step:
            logger.info("Skipping generation of SpikeArrest policy file because rate limiting is not enabled.")
            continue
        if "CORS.xml" in relative_path and not cors_enabled:
            logger.info("Skipping generation of CORS policy file because it is not enabled.")
            continue

        full_path = os.path.join(bundle_path, relative_path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        template_obj = Template(template_str)
        rendered_content = template_obj.render(**context)
        with open(full_path, "w") as f:
            f.write(rendered_content)

    logger.info("Generated apiproxy folder at: %s", bundle_path)
