import os
import sys
import logging
import kopf
import asyncio

sys.path.append("..")
from log_wrapper import LogWrapper, logwrapper

os.environ["HVAC_TOKEN"] = os.getenv("HVAC_TOKEN", "testtoken")

from secretsmanagementOperatorHC import (
    safe_get,
    secretsmanagementDelete,
    secretsmanagementCreate,
)


# Setup logging
logging_level = os.environ.get("LOGGING", logging.DEBUG)
root_logger = logging.getLogger()
root_logger.setLevel(logging.WARNING)
logger = logging.getLogger("SManOP")
logger.setLevel(int(logging_level))
logger.info(f"Logging set to %s", logging_level)

LogWrapper.set_defaultLogger(logger)

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


def test_secretsmanagementDelete():
    body_json_file = "testdata/CREATE-prodcat_cv.json"
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
            secretsmanagementDelete(meta, spec, status, body, namespace, labels, name)
        )
        loop.close()
    print(f"result: {result}")


def test_secretsmanagementCreate():
    body_json_file = "testdata/CREATE-prodcat_cv.json"
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
            secretsmanagementCreate(meta, spec, status, body, namespace, labels, name)
        )
        loop.close()
    print(f"finished")


def testLogWrapper():
    log = LogWrapper(logger)
    log.info("infolog")
    log.info("infolog", "with details")
    log.debug("debuglog")
    log.debug("debuglog", "with details")
    log.debug("debuglog", {"with": "details"})
    childLog = log.childLogger(
        function_name="fn", handler_name="hn", resource_name="rn", component_name="cn"
    )
    childLog.info("hi", "I am the child")
    childLog2 = childLog.childLogger(
        function_name="fn2",
        handler_name="hn2",
        resource_name="rn2",
        component_name="cn2",
    )
    childLog2.info("hi", "I am the child 2")
    childLog3 = childLog2.childLogger(function_name="fn3")
    childLog3.info("hi", "I am the child 3")


@logwrapper
def sync_func(logw=None):
    logw.info(f"I am sync_func")

@logwrapper(handler_name="synch")
def sync_func2(logw=None):
    logw.info(f"I am sync_func")

@logwrapper
async def async_func(logw=None):
    logw.info(f"I am async_func")

@logwrapper(handler_name="asynch")
async def async_func2(logw=None):
    logw.info(f"I am async_func")


#===============================================================================
# @logwrapper
# def ordinary1(logw):
#     try:
#         logw.info(f"I am ordinary1")
#         ordinary2("huhu", logw=logw)
#         x = None
#         x.show()
#     except Exception as ex:
#         print("--- INDIREKT ---")
#         logex(ex)
#         print("--- DIREKT ---")
#         print(f"{ex}: {traceback.format_exc()}")
# 
# 
# @logwrapper
# def ordinary2(text, logw="lll", magic=None):
#     logw.info(f"o2({text})")
#     ordinary3(logw)
# 
# 
# @logwrapper(handler_name="hn")
# def ordinary3(logw):
#     logw.info(f"I am ordinary3")
#     ordinary4("hoho", magic="xxx", logw=logw)
# 
# 
# @logwrapper(component_name="cn", resource_name="rn")
# def ordinary4(text, logw="lll", magic=None):
#     logw.info(f"o4({text}) with {magic}")
#     ordinary5("egal5", magic=5, logw=logw)
# 
# 
# @logwrapper(logger="other", component_name="cn", resource_name="rn")
# def ordinary5(text, logw="lll", magic=None):
#     logw.info(f"o5({text}) with {magic}")
#===============================================================================


async def async_main():
    await async_func()
    await async_func2()


if __name__ == "__main__":
    logging.info(f"main called")
    
    sync_func()
    sync_func2()
    asyncio.run(async_main())
    
    
    #===========================================================================
    # ordinary5("egal5", magic=5)
    # ordinary4("egal4", magic=2)
    # ordinary1("lw")
    # ordinary2("egal", magic=3, logw="jjj")
    # ordinary2("egal", magic=2)
    # ordinary3("lw")
    # ordinary4("egal", magic=3, logw="jjj")
    # ordinary4("egal4", magic=2)
    # testLogWrapper()
    #===========================================================================
    
    # ===========================================================================
    # k8s_load_config(proxy=False)
    # # k8s_load_vps2_config(proxy=True)
    # test_kubeconfig()
    # # test_secretsmanagementDelete()
    # test_secretsmanagementCreate()
    # ===========================================================================
