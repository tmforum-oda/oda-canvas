"""Unit tests for operator discovery on the portal's Operators page (issue #656)."""

from types import SimpleNamespace

import pytest

from auth.models import AuthUser
from k8s.resources import operators

NAMESPACE = "canvas"
USER = AuthUser(username="tester", email="tester@example.com")


def _deployment(
    name,
    containers=None,
    labels=None,
    annotations=None,
    namespace=NAMESPACE,
    replicas=1,
    ready_replicas=1,
):
    """Build a Deployment dict shaped like the kubernetes client's ``to_dict()`` output."""
    if containers is None:
        containers = [(name, f"registry.example.com/{name}:1.0.0")]
    return {
        "metadata": {
            "name": name,
            "namespace": namespace,
            "labels": labels or {},
            "annotations": annotations or {},
        },
        "spec": {
            "selector": {"match_labels": {"app": name}},
            "template": {
                "spec": {
                    "containers": [
                        {"name": cname, "image": image} for cname, image in containers
                    ]
                }
            },
            "strategy": {"type": "RollingUpdate"},
        },
        "status": {
            "replicas": replicas,
            "ready_replicas": ready_replicas,
            "available_replicas": ready_replicas,
            "updated_replicas": replicas,
        },
    }


def _pod(app, container_names, namespace=NAMESPACE, ready=True):
    """Build a Pod dict owned by the Deployment whose selector is ``app=<app>``."""
    return {
        "metadata": {
            "name": f"{app}-abc12",
            "namespace": namespace,
            "labels": {"app": app},
        },
        "spec": {
            "containers": [
                {"name": cname, "image": f"{cname}:1"} for cname in container_names
            ],
            "node_name": "node-1",
        },
        "status": {
            "phase": "Running",
            "conditions": [{"type": "Ready", "status": "True" if ready else "False"}],
            "container_statuses": [
                {
                    "name": cname,
                    "ready": ready,
                    "restart_count": 0,
                    "state": {"running": {}},
                }
                for cname in container_names
            ],
        },
    }


class _Item:
    def __init__(self, data):
        self._data = data

    def to_dict(self):
        return self._data


def _fake_cluster(monkeypatch, deployments, pods):
    """Route the module's Kubernetes API calls to in-memory Deployments and Pods."""

    def in_ns(items, namespace):
        return [i for i in items if i["metadata"]["namespace"] == namespace]

    def listing(items):
        return SimpleNamespace(items=[_Item(i) for i in items])

    apps = SimpleNamespace(
        list_deployment_for_all_namespaces=lambda: listing(deployments),
        list_namespaced_deployment=lambda ns: listing(in_ns(deployments, ns)),
    )
    core = SimpleNamespace(
        list_pod_for_all_namespaces=lambda: listing(pods),
        list_namespaced_pod=lambda ns: listing(in_ns(pods, ns)),
    )
    monkeypatch.setattr(operators, "get_impersonated_client", lambda user: object())
    monkeypatch.setattr(operators.client, "AppsV1Api", lambda api_client: apps)
    monkeypatch.setattr(operators.client, "CoreV1Api", lambda api_client: core)


def test_opt_in_label_lists_unknown_operator():
    deploy = _deployment("acme-operator", labels={operators.OPERATOR_LABEL: "true"})

    result = operators._deployment_to_operators(
        deploy, [_pod("acme-operator", ["acme-operator"])]
    )

    assert len(result) == 1
    op = result[0]
    assert op["name"] == "acme-operator"
    assert op["deploymentName"] == "acme-operator"
    assert op["containerName"] == "acme-operator"
    assert op["image"] == "registry.example.com/acme-operator:1.0.0"
    assert op["status"] == "running"
    assert op["tmfId"] is None
    assert len(op["pods"]) == 1


def test_operator_id_label_alone_opts_in():
    deploy = _deployment(
        "acme-operator", labels={operators.TMF_OPERATOR_LABEL_ID: "TMFOP042"}
    )

    [op] = operators._deployment_to_operators(deploy, [])

    assert op["name"] == "acme-operator"
    assert op["tmfId"] == "TMFOP042"
    assert op["tmfName"] is None


def test_operator_name_label_sets_display_and_tmf_name():
    deploy = _deployment(
        "acme-operator",
        labels={
            operators.TMF_OPERATOR_LABEL_ID: "TMFOP042",
            operators.TMF_OPERATOR_LABEL_NAME: "Acme-Operator",
        },
    )

    [op] = operators._deployment_to_operators(deploy, [])

    assert op["name"] == "Acme-Operator"
    assert op["deploymentName"] == "acme-operator"
    assert op["tmfName"] == "Acme-Operator"


def test_signature_match_without_labels_is_unchanged():
    deploy = _deployment(
        "canvas-component-operator",
        containers=[
            ("component-operator", "tmforumodacanvas/component-operator:1.0.0")
        ],
    )

    [op] = operators._deployment_to_operators(deploy, [])

    assert op["name"] == "component-operator"
    assert op["containerName"] == "component-operator"
    assert op["tmfId"] == "TMFOP001"
    assert op["tmfName"] == "Component Management Operator"


def test_deployment_without_label_or_signature_is_ignored():
    deploy = _deployment("my-web-app")

    assert operators._deployment_to_operators(deploy, []) == []


@pytest.mark.parametrize(
    "value, listed",
    [
        ("true", True),
        ("TRUE", True),
        ("True", True),
        ("false", False),
        ("", False),
        ("yes", False),
    ],
)
def test_opt_in_label_values(value, listed):
    deploy = _deployment("acme-operator", labels={operators.OPERATOR_LABEL: value})

    assert bool(operators._deployment_to_operators(deploy, [])) is listed


def test_empty_operator_id_does_not_opt_in():
    deploy = _deployment("acme-operator", labels={operators.TMF_OPERATOR_LABEL_ID: ""})

    assert operators._deployment_to_operators(deploy, []) == []


def test_label_wins_over_signature_match():
    deploy = _deployment(
        "component-operator",
        labels={
            operators.OPERATOR_LABEL: "true",
            operators.TMF_OPERATOR_LABEL_NAME: "Custom-Component-Operator",
        },
    )

    result = operators._deployment_to_operators(deploy, [])

    assert [op["name"] for op in result] == ["Custom-Component-Operator"]


def test_label_path_produces_one_operator_for_shared_deployment():
    deploy = _deployment(
        "shared-operators",
        containers=[
            ("component-operator", "component-operator:1"),
            ("api-operator-istio", "api-operator-istio:1"),
        ],
        labels={operators.OPERATOR_LABEL: "true"},
    )

    result = operators._deployment_to_operators(deploy, [])

    assert len(result) == 1
    assert result[0]["sharedDeployment"] is False


SIDECAR_CONTAINERS = [
    ("istio-proxy", "istio/proxyv2:1"),
    ("manager", "acme/manager:2"),
    ("acme-operator", "acme/operator:3"),
]


@pytest.mark.parametrize(
    "annotation, expected_container",
    [
        ("manager", "manager"),
        (None, "acme-operator"),
        ("does-not-exist", "acme-operator"),
    ],
)
def test_container_selection(annotation, expected_container):
    annotations = (
        {operators.OPERATOR_CONTAINER_ANNOTATION: annotation} if annotation else {}
    )
    deploy = _deployment(
        "acme-operator",
        containers=SIDECAR_CONTAINERS,
        labels={operators.OPERATOR_LABEL: "true"},
        annotations=annotations,
    )

    [op] = operators._deployment_to_operators(deploy, [])

    assert op["containerName"] == expected_container
    assert op["image"] == dict(SIDECAR_CONTAINERS)[expected_container]


def test_container_selection_uses_deployment_name_when_operator_name_differs():
    deploy = _deployment(
        "acme-operator",
        containers=SIDECAR_CONTAINERS,
        labels={
            operators.OPERATOR_LABEL: "true",
            operators.TMF_OPERATOR_LABEL_NAME: "Acme-Operator",
        },
    )

    [op] = operators._deployment_to_operators(deploy, [])

    assert op["name"] == "Acme-Operator"
    assert op["containerName"] == "acme-operator"


def test_container_selection_falls_back_to_first_container():
    deploy = _deployment(
        "acme",
        containers=[("main", "acme/main:1"), ("sidecar", "acme/sidecar:1")],
        labels={operators.OPERATOR_LABEL: "true"},
        annotations={operators.OPERATOR_CONTAINER_ANNOTATION: "missing"},
    )

    [op] = operators._deployment_to_operators(deploy, [])

    assert op["containerName"] == "main"


def test_deployment_without_containers():
    deploy = _deployment(
        "acme", containers=[], labels={operators.OPERATOR_LABEL: "true"}
    )

    [op] = operators._deployment_to_operators(deploy, [])

    assert op["containerName"] == ""
    assert op["image"] == ""


@pytest.mark.parametrize("ready", [True, False])
def test_counts_and_status_match_signature_path(ready):
    containers = [("component-operator", "component-operator:1")]
    pods = [_pod("component-operator", ["component-operator"], ready=ready)]
    plain = _deployment(
        "component-operator",
        containers=containers,
        replicas=1,
        ready_replicas=int(ready),
    )
    labelled = _deployment(
        "component-operator",
        containers=containers,
        labels={operators.OPERATOR_LABEL: "true"},
        replicas=1,
        ready_replicas=int(ready),
    )

    [by_signature] = operators._deployment_to_operators(plain, pods)
    [by_label] = operators._deployment_to_operators(labelled, pods)

    keys = ("containerName", "status", "desired", "ready", "available", "updated")
    assert {k: by_label[k] for k in keys} == {k: by_signature[k] for k in keys}
    assert by_label["status"] == ("running" if ready else "down")


def test_get_operator_finds_labelled_operator_by_name_and_deployment(monkeypatch):
    deploy = _deployment(
        "acme-operator",
        labels={
            operators.OPERATOR_LABEL: "true",
            operators.TMF_OPERATOR_LABEL_NAME: "Acme-Operator",
        },
    )
    _fake_cluster(monkeypatch, [deploy], [_pod("acme-operator", ["acme-operator"])])

    by_name = operators.get_operator("Acme-Operator", NAMESPACE, USER)
    by_deployment = operators.get_operator("acme-operator", NAMESPACE, USER)

    assert by_name is not None and by_name["name"] == "Acme-Operator"
    assert by_deployment is not None and by_deployment["name"] == "Acme-Operator"
    assert len(by_name["pods"]) == 1
    assert operators.get_operator("missing", NAMESPACE, USER) is None


def test_list_operators_sorts_known_operators_before_labelled(monkeypatch):
    deployments = [
        _deployment("aaa-operator", labels={operators.OPERATOR_LABEL: "true"}),
        _deployment("my-web-app"),
        _deployment("component-operator"),
    ]
    _fake_cluster(monkeypatch, deployments, [])

    result = operators.list_operators(USER)

    assert [op["name"] for op in result] == ["component-operator", "aaa-operator"]
