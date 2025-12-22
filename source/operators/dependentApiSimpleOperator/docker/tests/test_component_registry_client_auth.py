from dotenv import load_dotenv
load_dotenv()  # take environment variables

import pytest
import sys
import os


"""
preparation for local tests:

kubectl port-forward -n canvas svc/canvas-compreg 8080:80
export BASE_URL=http://localhost:8080

in RequestFileMocker initialization set recording=True to record new test data

deploy r-cat and f-cat from BDD tests:

helm upgrade --install r-cat -n components --create-namespace feature-definition-and-test-kit/testData/productcatalog-v1
helm upgrade --install f-cat -n components --create-namespace feature-definition-and-test-kit/testData/productcatalog-dependendent-API-v1
"""


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
## kubectl port-forward -n canvas svc/canvas-compreg 8080:80
BASE_URL = "http://localhost:8080"
RM_TESTDATA_FOLDER = "testdata/requests_compreg_mock"

INSTANCES = {}


@pytest.fixture
def rfmock() -> RequestFileMocker:
    if "rfm" not in INSTANCES:
        INSTANCES["rfm"] = RequestFileMocker(f"{RM_TESTDATA_FOLDER}-temp", BASE_URL, recording=True, allow_overwrite=True)
        # INSTANCES["rfm"] = RequestFileMocker(RM_TESTDATA_FOLDER, BASE_URL)
    return INSTANCES["rfm"]


@pytest.fixture
def comp_reg() -> ComponentRegistryClient:
    return ComponentRegistryClient(BASE_URL)


def getCharacteristicValue(characteristics, name):
    for charac in characteristics:
        if charac["name"] == name:
            return charac["value"]
    return None


def test_find_spec_success(comp_reg):  # , rfmock):
    oas_spec = "https://raw.githubusercontent.com/tmforum-apis/TMF620_ProductCatalog/master/TMF620-ProductCatalog-v4.0.0.swagger.json"
    # rfmock.mock_get("resource", f"find_spec_success", 200)
    comps = comp_reg.find_exposed_apis(oas_spec)
    # print(f"\nFOUND EXPOSED APIS:\n{json.dumps(comps,indent=2)}\n")
    assert len(comps) == 1
    assert comps[0]["name"] == "r-cat-productcatalogmanagement-productcatalogmanagement"
    assert comps[0]["category"] == "API"
    assert comps[0]["resourceRelationship"][0]["resource"]["id"] == "self:r-cat-productcatalogmanagement"
    assert getCharacteristicValue(comps[0]["resourceCharacteristic"], "url") == "https://components.ihc-dt.cluster-2.de/r-cat-productcatalogmanagement/tmf-api/productCatalogManagement/v4"
    assert getCharacteristicValue(comps[0]["resourceCharacteristic"], "specification")[0]["url"] == oas_spec

def test_find_spec_no_result(comp_reg):  # , rfmock):
    oas_spec = "https://invalid.oas/spec.json"
    # rfmock.mock_get("resource", f"find_spec_no_result", 200)
    comps = comp_reg.find_exposed_apis(oas_spec)
    # print(f"\nFOUND EXPOSED APIS:\n{json.dumps(comps,indent=2)}\n")
    assert len(comps) == 0


def test_get_upstream_registries(comp_reg):  # , rfmock):
    # rfmock.mock_get("hub", f"get_upstream_registries", 200)
    regs = comp_reg.get_upstream_registries()
    # print(f"\nUPSTREAM REGISTRIES:\n{json.dumps(regs,indent=2)}\n")
    assert len(regs) == 1
    assert regs[0] == "https://global-compreg.ihc-dt.cluster-2.de"


if __name__ == "__main__":
    # _clean_all()
    pytest.main(
        [
            "test_component_registry_client_auth.py",
            "-s",
            "-W",
            "ignore:Module already imported so cannot be rewritten:pytest.PytestAssertRewriteWarning",
        ]
    )
