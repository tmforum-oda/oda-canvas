from componentOperator import securityComponentVault, safe_get

import logging
import os
import kopf
import asyncio



# Setup logging
logging_level = os.environ.get('LOGGING', logging.DEBUG)
kopf_logger = logging.getLogger()
kopf_logger.setLevel(logging.WARNING)
logger = logging.getLogger('ComponentOperator')
logger.setLevel(int(logging_level))
logger.info(f'Logging set to %s', logging_level)

# ------------------- TESTS ---------------- #

import json 
import kubernetes.client




def k8s_load_config():
    if kubernetes.client.Configuration._default:
        return
    try:
        kubernetes.config.load_incluster_config()
        print("loaded incluster config")
    except kubernetes.config.ConfigException:
        try:
            kube_config_file = "~/.kube/config-vps5"
            proxy = "http://specialinternetaccess-lb.telekom.de:8080"
            kubernetes.config.load_kube_config(config_file = kube_config_file)
            kubernetes.client.Configuration._default.proxy = proxy 
            print("loaded config "+kube_config_file+" with proxy "+proxy)
        except kubernetes.config.ConfigException:
            try:
                kubernetes.config.load_kube_config()
                print("loaded default config")
            except kubernetes.config.ConfigException:
                raise Exception("Could not configure kubernetes python client")
    


def test_componentvault_extract():
    body_json_file = 'test/component/CREATE_component_body_with_vault.json'
    with open (body_json_file, 'r') as f:
        body = json.load(f)
    meta = body["metadata"]
    spec = body["spec"]
    status = safe_get(None, body, "status")
    patch = kopf.Patch({})
    warnings = []
    labels = safe_get(None, meta, 'labels')
    namespace = meta["namespace"]
    name = meta["name"]
    
    
    from kopf._cogs.structs.bodies import Body, RawBody, RawEvent, RawMeta
    from kopf._core.intents.causes import ChangingCause, Reason, WatchingCause
    from kopf._core.actions.execution import cause_var
    from kopf._core.engines.indexing import OperatorIndexers
    from kopf._cogs.structs.ephemera import Memo
    from kopf._core.actions.invocation import context
    
    OWNER_API_VERSION = 'owner-api-version'
    OWNER_NAMESPACE = 'owner-namespace'
    OWNER_KIND = 'OwnerKind'
    OWNER_NAME = 'owner-name'
    OWNER_UID = 'owner-uid'
    OWNER_LABELS = {'label-1': 'value-1', 'label-2': 'value-2'}
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

    resource = '?'
    cause = ChangingCause(
        logger=logging.getLogger('kopf.test.fake.logger'),
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
        loop.run_until_complete(securityComponentVault(meta, spec, status, body, namespace, labels, name))
        loop.close()


def test_componentvault_keep():
    body_json_file = 'test/component/UPDATE_component_body_with_vault_unchanged.json'
    with open (body_json_file, 'r') as f:
        body = json.load(f)
    meta = body["metadata"]
    spec = body["spec"]
    status = safe_get(None, body, "status")
    patch = kopf.Patch({})
    warnings = []
    labels = safe_get(None, meta, 'labels')
    namespace = meta["namespace"]
    name = meta["name"]
    
    
    from kopf._cogs.structs.bodies import Body, RawBody, RawEvent, RawMeta
    from kopf._core.intents.causes import ChangingCause, Reason, WatchingCause
    from kopf._core.actions.execution import cause_var
    from kopf._core.engines.indexing import OperatorIndexers
    from kopf._cogs.structs.ephemera import Memo
    from kopf._core.actions.invocation import context
    
    OWNER_API_VERSION = 'owner-api-version'
    OWNER_NAMESPACE = 'owner-namespace'
    OWNER_KIND = 'OwnerKind'
    OWNER_NAME = 'owner-name'
    OWNER_UID = 'owner-uid'
    OWNER_LABELS = {'label-1': 'value-1', 'label-2': 'value-2'}
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

    resource = '?'
    cause = ChangingCause(
        logger=logging.getLogger('kopf.test.fake.logger'),
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
        loop.run_until_complete(securityComponentVault(meta, spec, status, body, namespace, labels, name))
        loop.close()



if __name__ == '__main__':
    logging.info(f"main called")
    k8s_load_config()
    #test_componentvault_extract()
    test_componentvault_keep()
    

