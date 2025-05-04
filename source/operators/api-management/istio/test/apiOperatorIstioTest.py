import os
import sys
import logging
import kopf
import asyncio

sys.path.append("..")

from apiOperatorIstio import apiStatus, implementation_status


# Setup logging
logging_level = os.environ.get("LOGGING", logging.DEBUG)
root_logger = logging.getLogger()
root_logger.setLevel(logging.WARNING)
logger = logging.getLogger("SManOP")
logger.setLevel(int(logging_level))
logger.info(f"Logging set to %s", logging_level)


# ------------------- HELPERS -------------- #


def safe_get(default_value, dictionary, *paths):
    result = dictionary
    for path in paths:
        if path not in result:
            return default_value
        result = result[path]
    return result


# ------------------- TESTS ---------------- #

import json
import kubernetes.client


def test_kubeconfig():
    v1 = kubernetes.client.CoreV1Api()
    nameSpaceList = v1.list_namespace()
    for nameSpace in nameSpaceList.items:
        print(nameSpace.metadata.name)


def k8s_load_config(proxy=False):
    if kubernetes.client.Configuration._default:
        return
    try:
        kubernetes.config.load_incluster_config()
        print("loaded incluster config")
    except kubernetes.config.ConfigException:
        # try:
        #    kube_config_file = "~/.kube/config-vps5"
        #    kubernetes.config.load_kube_config(config_file=kube_config_file)
        # except kubernetes.config.ConfigException:
        try:
            kubernetes.config.load_kube_config()
            print("loaded default config")
        except kubernetes.config.ConfigException:
            raise Exception("Could not configure kubernetes python client")
        if proxy:
            proxy = os.environ["HTTPS_PROXY"]
            kubernetes.client.Configuration._default.proxy = proxy
            print(f"set proxy to {proxy}")


def k8s_load_vps2_config(proxy=True):
    if kubernetes.client.Configuration._default:
        return
    try:
        kube_config_file = "~/.kube/config.vps2"
        kubernetes.config.load_kube_config(config_file=kube_config_file)
    except kubernetes.config.ConfigException:
        raise Exception("Could not configure kubernetes python client")
    if proxy:
        proxy = os.environ["HTTPS_PROXY"]
        kubernetes.client.Configuration._default.proxy = proxy
        print(f"set proxy to {proxy}")


def test_apiStatusCreate(json_body_filename):
    body_json_file = json_body_filename
    with open(body_json_file, "r") as f:
        body = json.load(f)
    meta = body["metadata"]
    spec = body["spec"]
    status = safe_get(None, body, "status")
    patch = kopf.Patch({})
    warnings = []
    labels = safe_get(None, meta, "labels")
    namespace = meta["namespace"]
    name = meta["name"]

    from kopf._cogs.structs.bodies import Body, RawBody, RawEvent, RawMeta
    from kopf._core.intents.causes import ChangingCause, Reason, WatchingCause
    from kopf._core.actions.execution import cause_var
    from kopf._core.engines.indexing import OperatorIndexers
    from kopf._cogs.structs.ephemera import Memo
    from kopf._core.actions.invocation import context

    OWNER_API_VERSION = "owner-api-version"
    OWNER_NAMESPACE = "owner-namespace"
    OWNER_KIND = "OwnerKind"
    OWNER_NAME = "owner-name"
    OWNER_UID = "owner-uid"
    OWNER_LABELS = {"label-1": "value-1", "label-2": "value-2"}
    OWNER = RawBody(
        apiVersion=OWNER_API_VERSION,
        kind=OWNER_KIND,
        metadata=RawMeta(
            namespace=OWNER_NAMESPACE,
            name=OWNER_NAME,
            uid=OWNER_UID,
            labels=OWNER_LABELS,
        ),
    )

    resource = "?"
    cause = ChangingCause(
        logger=logging.getLogger("kopf.test.fake.logger"),
        indices=OperatorIndexers().indices,
        resource=resource,
        patch=patch,
        memo=Memo(),
        body=body,
        initial=False,
        reason=Reason.NOOP,
    )
    with context([(cause_var, cause)]):
        loop = asyncio.get_event_loop()
        result = loop.run_until_complete(
            apiStatus(meta, spec, status, namespace, labels, name, body)
        )
        loop.close()
    print(f"result: {result}")


def test_implementation_status(json_body_filename):
    body_json_file = json_body_filename
    with open(body_json_file, "r") as f:
        body = json.load(f)
    meta = body["metadata"]
    spec = safe_get(None, body, "spec")
    status = safe_get(None, body, "status")
    patch = kopf.Patch({})
    warnings = []
    labels = safe_get(None, meta, "labels")
    namespace = meta["namespace"]
    name = meta["name"]

    from kopf._cogs.structs.bodies import Body, RawBody, RawEvent, RawMeta
    from kopf._core.intents.causes import ChangingCause, Reason, WatchingCause
    from kopf._core.actions.execution import cause_var
    from kopf._core.engines.indexing import OperatorIndexers
    from kopf._cogs.structs.ephemera import Memo
    from kopf._core.actions.invocation import context

    OWNER_API_VERSION = "owner-api-version"
    OWNER_NAMESPACE = "owner-namespace"
    OWNER_KIND = "OwnerKind"
    OWNER_NAME = "owner-name"
    OWNER_UID = "owner-uid"
    OWNER_LABELS = {"label-1": "value-1", "label-2": "value-2"}
    OWNER = RawBody(
        apiVersion=OWNER_API_VERSION,
        kind=OWNER_KIND,
        metadata=RawMeta(
            namespace=OWNER_NAMESPACE,
            name=OWNER_NAME,
            uid=OWNER_UID,
            labels=OWNER_LABELS,
        ),
    )

    resource = "?"
    cause = ChangingCause(
        logger=logging.getLogger("kopf.test.fake.logger"),
        indices=OperatorIndexers().indices,
        resource=resource,
        patch=patch,
        memo=Memo(),
        body=body,
        initial=False,
        reason=Reason.NOOP,
    )
    with context([(cause_var, cause)]):
        loop = asyncio.get_event_loop()
        result = loop.run_until_complete(
            implementation_status(meta, spec, status, body, namespace, labels, name)
        )
        loop.close()
    print(f"result: {result}")


if __name__ == "__main__":
    logging.info(f"main called")

    k8s_load_config(proxy=False)
    # k8s_load_vps2_config(proxy=True)
    test_kubeconfig()
    # test_secretsmanagementDelete()
    # test_secretsmanagementCreate()
    # test_apiStatusCreate("testdata/CREATE_APISTATUS.json")
    # test_apiStatusCreate("testdata/CREATE_APISTATUS_2.json")
    # test_apiStatusCreate("testdata/CREATE_APISTATUS_3.json")
    test_apiStatusCreate("testdata/CREATE_APISTATUS_4.json")
    # test_implementation_status("testdata/ENDPOINTSLICE_prodcat_ready.json")
