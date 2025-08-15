# To run this using Flask:
# 1) set the environment variable
#    $env:FLASK_APP = 'securityControllerAPIserver-keycloak.py'
# 2) type 'flask run'

from waitress import serve
from flask import Flask
from flask import request
import logging
import os
import uuid
import datetime

from keycloakUtils import Keycloak

from cloudevents.http import CloudEvent, to_structured

# Helper functions -------------------------------------------------------


def format_cloud_event(message: str, subject: str) -> str:
    """
    Returns a correctly formatted CloudEvents compliant event
    """
    attributes = {
        "specversion": "1.0",
        "type": "org.tmforum.for.type.event.an.invented.burton.brian",
        "source": "https://example.com/security-controller",
        "subject": subject,
        "id": str(uuid.uuid4()),
        "time": datetime.datetime.now().isoformat(),
        "datacontenttype": "application/json",
    }

    data = {"message": message}

    event = CloudEvent(attributes, data)
    _, body = to_structured(event)

    return body


# Initial setup ----------------------------------------------------------

logging_level = os.environ.get("LOGGING", 10)
username = os.environ.get("KEYCLOAK_USER")
password = os.environ.get("KEYCLOAK_PASSWORD")
kcBaseURL = os.environ.get("KEYCLOAK_BASE")
kcRealm = os.environ.get("KEYCLOAK_REALM")
logger = logging.getLogger()
logger.setLevel(int(logging_level))  # Logging level default = INFO
logger.info("Logging set to %s", logging_level)

PARTY_ROLE_CREATION = "PartyRoleCreationNotification"
PARTY_ROLE_UPDATE = "PartyRoleAttributeValueChangeNotification"
PARTY_ROLE_DELETION = "PartyRoleRemoveNotification"

PERMISSION_SPEC_SET_CREATION = "PermissionSpecificationSetCreationNotification"
PERMISSION_SPEC_SET_UPDATE = "PermissionSpecificationSetAttributeValueChangeNotification"
PERMISSION_SPEC_SET_DELETION = "PermissionSpecificationSetRemoveNotification"

kc = Keycloak(kcBaseURL)

# Flask app --------------------------------------------------------------

app = Flask(__name__)


@app.route("/listener", methods=["POST"])
def party_role_listener():
    client = ""
    doc = request.json
    logger.debug("security-APIListener received %s", doc)
    party_role = doc["event"]["partyRole"]
    logger.debug("partyRole = %s", party_role)
    if party_role["@baseType"] == "PartyRole":
        event_type = doc["eventType"]
        logger.debug("security-APIListener called with eventType %s", event_type)
        component = party_role["href"].split("/")[3]

        try:  # to authenticate and get a token
            token = kc.get_token(username, password)
        except RuntimeError as e:
            logger.error(
                format_cloud_event(
                    str(e), "security-APIListener could not GET Keycloak token"
                )
            )
            raise

        try:  # to get the list of existing clients
            client_list = kc.get_client_list(token, kcRealm)
        except RuntimeError as e:
            logger.error(
                format_cloud_event(
                    str(e), f"security-APIListener could not GET clients for {kcRealm}"
                )
            )
        else:
            client = client_list[component]

        if client != "":
            if event_type == PARTY_ROLE_CREATION:
                try:  # to add the role to the client in Keycloak
                    kc.add_role(party_role["name"], client, token, kcRealm)
                except RuntimeError as e:
                    logger.error(
                        format_cloud_event(
                            f'Keycloak role create failed for {party_role["name"]} in {component}',
                            "security-APIListener event listener error",
                        )
                    )
                else:
                    logger.info(
                        format_cloud_event(
                            f'Keycloak role {party_role["name"]} added to {component}',
                            "security-APIListener event listener success",
                        )
                    )
            elif event_type == PARTY_ROLE_DELETION:
                try:  # to add the role to the client in Keycloak
                    kc.del_role(party_role["name"], client, token, kcRealm)
                except RuntimeError:
                    logger.error(
                        format_cloud_event(
                            f'Keycloak role delete failed for {party_role["name"]} in {component}',
                            "security-APIListener event listener error",
                        )
                    )
                else:
                    logger.info(
                        format_cloud_event(
                            f'Keycloak role {party_role["name"]} removed from {component}',
                            "security-APIListener event listener success",
                        )
                    )
            elif event_type == PARTY_ROLE_UPDATE:
                pass  # because we do not need to do anything for updates
                logger.debug("Update Keycloak for UPDATE")
            else:
                logger.warning(
                    format_cloud_event(
                        f"eventType was {event_type} - not processed",
                        "security-APIListener called with invalid eventType",
                    )
                )
        else:
            logger.error(
                format_cloud_event(
                    f'No client found in Keycloak for {party_role["name"]}',
                    "security-APIListener called for non-existent client",
                )
            )
    else:
        logger.warning(
            format_cloud_event(
                f'@baseType was {party_role["@baseType"]} - not processed',
                "security-APIListener called with invalid @baseType",
            )
        )

    return ""


def handle_permission_spec_set_event(doc):
    """
    Handle permission specification set events and create/update/delete roles in Keycloak
    """
    client = ""
    logger.debug("security-APIListener received permissionSpecificationSet event %s", doc)
    permission_spec_set = doc["event"]["permissionSpecificationSet"]
    logger.debug("permissionSpecificationSet = %s", permission_spec_set)
    
    if permission_spec_set["@baseType"] == "PermissionSpecificationSet":
        event_type = doc["eventType"]
        logger.debug("security-APIListener called with eventType %s", event_type)
        component = permission_spec_set["href"].split("/")[3]

        try:  # to authenticate and get a token
            token = kc.get_token(username, password)
        except RuntimeError as e:
            logger.error(
                format_cloud_event(
                    str(e), "security-APIListener could not GET Keycloak token for permissionSpecificationSet"
                )
            )
            raise

        try:  # to get the list of existing clients
            client_list = kc.get_client_list(token, kcRealm)
        except RuntimeError as e:
            logger.error(
                format_cloud_event(
                    str(e), f"security-APIListener could not GET clients for {kcRealm} (permissionSpecificationSet)"
                )
            )
        else:
            client = client_list[component]

        if client != "":
            if event_type == PERMISSION_SPEC_SET_CREATION:
                try:  # to add the role to the client in Keycloak
                    description = permission_spec_set.get("description")
                    kc.add_role(permission_spec_set["name"], client, token, kcRealm, description)
                except RuntimeError as e:
                    logger.error(
                        format_cloud_event(
                            f'Keycloak role create failed for {permission_spec_set["name"]} in {component}',
                            "security-APIListener permissionSpecificationSet event listener error",
                        )
                    )
                else:
                    logger.info(
                        format_cloud_event(
                            f'Keycloak role {permission_spec_set["name"]} added to {component}',
                            "security-APIListener permissionSpecificationSet event listener success",
                        )
                    )
            elif event_type == PERMISSION_SPEC_SET_DELETION:
                try:  # to delete the role from the client in Keycloak
                    kc.del_role(permission_spec_set["name"], client, token, kcRealm)
                except RuntimeError:
                    logger.error(
                        format_cloud_event(
                            f'Keycloak role delete failed for {permission_spec_set["name"]} in {component}',
                            "security-APIListener permissionSpecificationSet event listener error",
                        )
                    )
                else:
                    logger.info(
                        format_cloud_event(
                            f'Keycloak role {permission_spec_set["name"]} removed from {component}',
                            "security-APIListener permissionSpecificationSet event listener success",
                        )
                    )
            elif event_type == PERMISSION_SPEC_SET_UPDATE:
                pass  # because we do not need to do anything for updates
                logger.debug("Update Keycloak for permissionSpecificationSet UPDATE")
            else:
                logger.warning(
                    format_cloud_event(
                        f"eventType was {event_type} - not processed for permissionSpecificationSet",
                        "security-APIListener called with invalid eventType for permissionSpecificationSet",
                    )
                )
        else:
            logger.error(
                format_cloud_event(
                    f'No client found in Keycloak for {permission_spec_set["name"]}',
                    "security-APIListener called for non-existent client (permissionSpecificationSet)",
                )
            )
    else:
        logger.warning(
            format_cloud_event(
                f'@baseType was {permission_spec_set["@baseType"]} - not processed for permissionSpecificationSet',
                "security-APIListener called with invalid @baseType for permissionSpecificationSet",
            )
        )


@app.route("/listener", methods=["POST"])
def unified_listener():
    """
    Unified listener that handles both partyRole and permissionSpecificationSet events
    """
    doc = request.json
    logger.debug("security-APIListener received %s", doc)
    
    # Check if this is a partyRole event
    if "partyRole" in doc.get("event", {}):
        return party_role_handler(doc)
    # Check if this is a permissionSpecificationSet event
    elif "permissionSpecificationSet" in doc.get("event", {}):
        handle_permission_spec_set_event(doc)
        return ""
    else:
        logger.warning(
            format_cloud_event(
                "Unknown event type received",
                "security-APIListener received unknown event structure",
            )
        )
        return ""


def party_role_handler(doc):
    """
    Extract the original party role handling logic
    """
    client = ""
    party_role = doc["event"]["partyRole"]
    logger.debug("partyRole = %s", party_role)
    if party_role["@baseType"] == "PartyRole":
        event_type = doc["eventType"]
        logger.debug("security-APIListener called with eventType %s", event_type)
        component = party_role["href"].split("/")[3]

        try:  # to authenticate and get a token
            token = kc.get_token(username, password)
        except RuntimeError as e:
            logger.error(
                format_cloud_event(
                    str(e), "security-APIListener could not GET Keycloak token"
                )
            )
            raise

        try:  # to get the list of existing clients
            client_list = kc.get_client_list(token, kcRealm)
        except RuntimeError as e:
            logger.error(
                format_cloud_event(
                    str(e), f"security-APIListener could not GET clients for {kcRealm}"
                )
            )
        else:
            client = client_list[component]

        if client != "":
            if event_type == PARTY_ROLE_CREATION:
                try:  # to add the role to the client in Keycloak
                    kc.add_role(party_role["name"], client, token, kcRealm)
                except RuntimeError as e:
                    logger.error(
                        format_cloud_event(
                            f'Keycloak role create failed for {party_role["name"]} in {component}',
                            "security-APIListener event listener error",
                        )
                    )
                else:
                    logger.info(
                        format_cloud_event(
                            f'Keycloak role {party_role["name"]} added to {component}',
                            "security-APIListener event listener success",
                        )
                    )
            elif event_type == PARTY_ROLE_DELETION:
                try:  # to add the role to the client in Keycloak
                    kc.del_role(party_role["name"], client, token, kcRealm)
                except RuntimeError:
                    logger.error(
                        format_cloud_event(
                            f'Keycloak role delete failed for {party_role["name"]} in {component}',
                            "security-APIListener event listener error",
                        )
                    )
                else:
                    logger.info(
                        format_cloud_event(
                            f'Keycloak role {party_role["name"]} removed from {component}',
                            "security-APIListener event listener success",
                        )
                    )
            elif event_type == PARTY_ROLE_UPDATE:
                pass  # because we do not need to do anything for updates
                logger.debug("Update Keycloak for UPDATE")
            else:
                logger.warning(
                    format_cloud_event(
                        f"eventType was {event_type} - not processed",
                        "security-APIListener called with invalid eventType",
                    )
                )
        else:
            logger.error(
                format_cloud_event(
                    f'No client found in Keycloak for {party_role["name"]}',
                    "security-APIListener called for non-existent client",
                )
            )
    else:
        logger.warning(
            format_cloud_event(
                f'@baseType was {party_role["@baseType"]} - not processed',
                "security-APIListener called with invalid @baseType",
            )
        )

    return ""


if __name__ == "__main__":
    serve(app, host="0.0.0.0", port=5000)
