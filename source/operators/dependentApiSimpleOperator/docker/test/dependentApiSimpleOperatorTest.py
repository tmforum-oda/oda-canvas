import os
import sys
import logging
import kopf
import asyncio

os.environ["CANVAS_INFO_ENDPOINT"] = "https://canvas-info.ihc-dt.cluster-3.de/tmf-api/serviceInventoryManagement/v5"

sys.path.append("../src")
from dependentApiSimpleOperator import (
    dependentApiCreate,
    dependentApiDelete,
    updateDepedentAPIReady,
)


# Setup logging
logging_level = os.environ.get("LOGGING", logging.DEBUG)
kopf_logger = logging.getLogger()
kopf_logger.setLevel(logging.INFO)
logger = logging.getLogger("DependentApiSimpleOperator")
logger.setLevel(int(logging_level))
logger.info(f"Logging set to %s", logging_level)

# ------------------- TESTS ---------------- #

import json
import kubernetes.client


def safe_get(default_value, dictionary, *paths):
    result = dictionary
    for path in paths:
        if path not in result:
            return default_value
        result = result[path]
    return result


def set_proxy():
    os.environ["HTTP_PROXY"] = "http://specialinternetaccess-lb.telekom.de:8080"
    os.environ["HTTPS_PROXY"] = "http://specialinternetaccess-lb.telekom.de:8080"
    os.environ["NO_PROXY"] = (
        "10.0.0.0/8,.eks.amazonaws.com,.aws.telekom.de,caas-portal-test.telekom.de,caas-portal.telekom.de,.caas-t02.telekom.de"
    )


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


def test_dependentApiCreate():
    body_json_file = "testdata/CREATE_prodcat.json"
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
        loop.run_until_complete(
            dependentApiCreate(meta, spec, status, body, namespace, labels, name)
        )
        loop.close()


def test_dependentApiUpdate():
    body_json_file = "testdata/UPDATE_prodcat.json"
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
        loop.run_until_complete(
            dependentApiCreate(meta, spec, status, body, namespace, labels, name)
        )
        loop.close()


def test_dependentApiDelete():
    body_json_file = "testdata/CREATE_prodcat.json"
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
        loop.run_until_complete(
            dependentApiDelete(meta, spec, status, body, namespace, labels, name)
        )
        loop.close()


def test_updateDepedentAPIReady():
    body_json_file = "testdata/UPDATE_prodcat_ready.json"
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
        loop.run_until_complete(
            updateDepedentAPIReady(meta, spec, status, body, namespace, labels, name)
        )
        loop.close()


if __name__ == "__main__":
    logging.info(f"main called")
    k8s_load_config(proxy=True)
    test_kubeconfig()
    test_dependentApiCreate()
    # test_dependentApiUpdate()
    # test_dependentApiDelete()
    # test_updateDepedentAPIReady()
