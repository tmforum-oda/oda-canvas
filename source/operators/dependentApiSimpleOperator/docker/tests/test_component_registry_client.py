import pytest
import sys
import os

try:
    import component_reg_client
except ModuleNotFoundError:
    # allow running component locally without setting PYTHONPATH
    sys.path.append(
        os.path.abspath(
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "../src")
        )
    )
    import component_reg_client

from request_file_mocker import RequestFileMocker

from component_reg_client import ComponentRegistryClient
import json


## for local tests to the cluster use:
## kubectl port-forward -n canvas svc/info 8638:80
BASE_URL = "http://localhost:8080"
RM_TESTDATA_FOLDER = "testdata/requests_compreg_mock"

INSTANCES = {}


@pytest.fixture
def rfmock() -> RequestFileMocker:
    if "rfm" not in INSTANCES:
        # INSTANCES["rfm"] = RequestFileMocker(RM_TESTDATA_FOLDER, BASE_URL, recording=True, allow_overwrite=True)
        INSTANCES["rfm"] = RequestFileMocker(RM_TESTDATA_FOLDER, BASE_URL)
    return INSTANCES["rfm"]


@pytest.fixture
def comp_reg() -> ComponentRegistryClient:
    return ComponentRegistryClient(BASE_URL)


def test_find_spec_success(comp_reg, rfmock):
    oas_spec = "https://raw.githubusercontent.com/tmforum-apis/TMF620_ProductCatalog/master/TMF620-ProductCatalog-v4.0.0.swagger.json"
    rfmock.mock_get("components/by-oas-specification", f"find_spec_success", 200)
    comps = comp_reg.find_exposed_apis(oas_spec)
    # print(f"\nFOUND EXPOSED APIS:\n{json.dumps(comps,indent=2)}\n")
    assert len(comps) == 1
    assert comps[0]["component_name"] == "demo-a-productcatalogmanagement"
    assert comps[0]["component_registry_ref"] == "self"
    exp_apis = comps[0]["exposed_apis"]
    assert len(exp_apis) == 1
    exp_api = exp_apis[0]
    assert exp_api["oas_specification"] ==  oas_spec
    assert exp_api["url"] == "https://components.ihc-dt.cluster-2.de/demo-a-productcatalogmanagement/tmf-api/productCatalogManagement/v4"


def test_find_spec_no_result(comp_reg, rfmock):
    oas_spec = "https://invalid.oas/spec.json"
    rfmock.mock_get("components/by-oas-specification", f"find_spec_no_result", 200)
    comps = comp_reg.find_exposed_apis(oas_spec)
    # print(f"\nFOUND EXPOSED APIS:\n{json.dumps(comps,indent=2)}\n")
    assert len(comps) == 0


def test_get_upstream_registries(comp_reg, rfmock):
    rfmock.mock_get("registries/by-type/upstream", f"get_upstream_registries", 200)
    regs = comp_reg.get_upstream_registries()
    # print(f"\nUPSTREAM REGISTRIES:\n{json.dumps(regs,indent=2)}\n")
    assert len(regs) == 1
    assert regs[0] == "https://compreg-a.ihc-dt.cluster-2.de"


if __name__ == "__main__":
    # _clean_all()
    pytest.main(
        [
            "test_component_registry_client.py",
            "-s",
            "-W",
            "ignore:Module already imported so cannot be rewritten:pytest.PytestAssertRewriteWarning",
        ]
    )
