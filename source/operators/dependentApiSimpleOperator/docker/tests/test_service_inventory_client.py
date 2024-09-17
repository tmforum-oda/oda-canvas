import pytest
import sys
import os

try:
    import service_inventory_client
except ModuleNotFoundError:
    # allow running component locally without setting PYTHONPATH
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '../src')))
    import service_inventory_client

from request_file_mocker import RequestFileMocker

from service_inventory_client import ServiceInventoryAPI
import json


BASE_URL="https://canvas-info.ihc-dt.cluster-3.de/tmf-api/serviceInventoryManagement/v5"
RM_TESTDATA_FOLDER = "testdata/requests_mock"

INSTANCES = {}

@pytest.fixture
def rfmock()->RequestFileMocker:
    if "rfm" not in INSTANCES:
        #INSTANCES["rfm"] = RequestFileMocker(RM_TESTDATA_FOLDER, BASE_URL, recording=True, allow_overwrite=True)
        INSTANCES["rfm"] = RequestFileMocker(RM_TESTDATA_FOLDER, BASE_URL)
    return INSTANCES["rfm"]


@pytest.fixture
def svc_inv()->ServiceInventoryAPI:
    return ServiceInventoryAPI(BASE_URL)


def _clean_all():
    svc_inv = ServiceInventoryAPI(BASE_URL)
    svcs = svc_inv.list_services(state=None)
    ids = [svc["id"] for svc in svcs]
    for id in ids:
        print(f"deleting service {id}")
        svc_inv.delete_service(id)
    
    
def assert_ids(svc_list, id_list):
    expected_id_list = sorted(id_list)
    actual_id_list = sorted([svc["id"] for svc in svc_list])
    assert expected_id_list == actual_id_list, f"objects not equal:\nEXPECTED: {expected_id_list}\nACTUAL:   {actual_id_list}"


def create_service_1(svc_inv, rfmock, name):
    """
    service 1: active acme downstream
    """ 
    rfmock.mock_post('service', f"create-svc1-{name}", 201)
    svc1 = svc_inv.create_service(
        componentName="acme-productinventory", 
        dependencyName="downstreamproductcatalog", 
        url="http://components.ihc-dt.cluster-3.de/alice-productcatalogmanagement/tmf-api/productCatalogManagement/v4",
        specification="https://raw.githubusercontent.com/tmforum-apis/TMF620_ProductCatalog/master/TMF620-ProductCatalog-v4.0.0.swagger.json",
        state="active")
    print(f"\nCREATED active acme downstream SERVICE 1:\n{json.dumps(svc1,indent=2)}\n")
    id1 = svc1["id"]
    assert svc1 == {
      "id": id1,
      "state": "active",
      "componentName": "acme-productinventory",
      "dependencyName": "downstreamproductcatalog",
      "url": "http://components.ihc-dt.cluster-3.de/alice-productcatalogmanagement/tmf-api/productCatalogManagement/v4",
      "OASSpecification": "https://raw.githubusercontent.com/tmforum-apis/TMF620_ProductCatalog/master/TMF620-ProductCatalog-v4.0.0.swagger.json"
    }
    return id1

def create_service_2(svc_inv, rfmock, name):
    """
    service 2: inactive bcme downstream
    """ 
    rfmock.mock_post('service', f"create-svc2-{name}", 201)
    svc2 = svc_inv.create_service(
        componentName="bcme-productinventory", 
        dependencyName="downstreamproductcatalog", 
        url="http://components.ihc-dt.cluster-3.de/alice-productcatalogmanagement/tmf-api/productCatalogManagement/v4",
        specification="https://raw.githubusercontent.com/tmforum-apis/TMF620_ProductCatalog/master/TMF620-ProductCatalog-v4.0.0.swagger.json",
        state="inactive")
    print(f"\nCREATED inactive bcme downstream SERVICE 2:\n{json.dumps(svc2,indent=2)}\n")
    id2 = svc2["id"]
    assert svc2 == {
      "id": id2,
      "state": "inactive",
      "componentName": "bcme-productinventory",
      "dependencyName": "downstreamproductcatalog",
      "url": "http://components.ihc-dt.cluster-3.de/alice-productcatalogmanagement/tmf-api/productCatalogManagement/v4",
      "OASSpecification": "https://raw.githubusercontent.com/tmforum-apis/TMF620_ProductCatalog/master/TMF620-ProductCatalog-v4.0.0.swagger.json"
    }
    return id2


def create_service_3(svc_inv, rfmock, name):
    """
    service 3: active bcme upstream
    """ 
    rfmock.mock_post('service', f"create-svc3-{name}", 201)
    svc3 = svc_inv.create_service(
        componentName="bcme-productinventory",
        dependencyName="upstreamproductcatalog",
        url="http://components.ihc-dt.cluster-3.de/alice-productcatalogmanagement/tmf-api/productCatalogManagement/v4",
        specification="https://raw.githubusercontent.com/tmforum-apis/TMF620_ProductCatalog/master/TMF620-ProductCatalog-v4.0.0.swagger.json",
        state="active")
    print(f"\nCREATED active bcme upstream SERVICE 3:\n{json.dumps(svc3,indent=2)}\n")
    id3 = svc3["id"]
    assert svc3 == {
      "id": id3,
      "state": "active",
      "componentName": "bcme-productinventory",
      "dependencyName": "upstreamproductcatalog",
      "url": "http://components.ihc-dt.cluster-3.de/alice-productcatalogmanagement/tmf-api/productCatalogManagement/v4",
      "OASSpecification": "https://raw.githubusercontent.com/tmforum-apis/TMF620_ProductCatalog/master/TMF620-ProductCatalog-v4.0.0.swagger.json"
    }
    return id3 
   

def delete_service_1(svc_inv, rfmock, id1, name):
    rfmock.mock_delete(f'service/{id1}', f'svc1-{name}', 204)
    ok = svc_inv.delete_service(id1)
    assert ok == True
    print(f"\ndeleted service-1")

def delete_service_2(svc_inv, rfmock, id2, name):
    rfmock.mock_delete(f'service/{id2}', f'svc2-{name}', 204)
    ok = svc_inv.delete_service(id2)
    assert ok == True
    print(f"\ndeleted service-2")

def delete_service_3(svc_inv, rfmock, id3, name):
    rfmock.mock_delete(f'service/{id3}', f'svc3-{name}', 204)
    ok = svc_inv.delete_service(id3)
    assert ok == True
    print(f"\ndeleted service-3")


def test_create_and_delete_service(svc_inv, rfmock):
    id1 = create_service_1(svc_inv, rfmock, "createdelete")
    delete_service_1(svc_inv, rfmock, id1, "createdelete")


def test_delete_non_existent_service(svc_inv, rfmock):
    rfmock.mock_delete(f'service/unknown', f'unknown', 500)
    ok = svc_inv.delete_service("unknown", ignore_not_found=True)
    assert ok == False

    try:
        rfmock.mock_delete(f'service/unknown', f'unknown', 500)
        svc_inv.delete_service("unknown")
        assert False, "delete did not fail with ignore_not_found=False"
    except ValueError as e:
        assert "Unexpected http status code" in e.args[0]


def test_create_invalid_state(svc_inv, rfmock):
    rfmock.mock_post('service', "create-invalid-state", 400)
    try:
        svc1 = svc_inv.create_service(
            componentName="acme-productinventory", 
            dependencyName="downstreamproductcatalog", 
            url="http://components.ihc-dt.cluster-3.de/alice-productcatalogmanagement/tmf-api/productCatalogManagement/v4",
            specification="https://raw.githubusercontent.com/tmforum-apis/TMF620_ProductCatalog/master/TMF620-ProductCatalog-v4.0.0.swagger.json",
            state="fictitious")
        assert False, "service was created with invalid state"
    except ValueError as e:
        assert "Unexpected http status code 400" in e.args[0]
        assert "request.body.state should be equal to one of the allowed values" in e.args[0]


def test_get_service(svc_inv, rfmock):
    id1 = create_service_1(svc_inv, rfmock, "getsvc")

    rfmock.mock_get(f'service/{id1}', 'id-svc1', 200)
    svc1b = svc_inv.get_service(id1)
    print(f"\nGET service-1 BY ID:\n{json.dumps(svc1b, indent=2)}")
    assert svc1b == {
      "id": id1,
      "state": "active",
      "componentName": "acme-productinventory",
      "dependencyName": "downstreamproductcatalog",
      "url": "http://components.ihc-dt.cluster-3.de/alice-productcatalogmanagement/tmf-api/productCatalogManagement/v4",
      "OASSpecification": "https://raw.githubusercontent.com/tmforum-apis/TMF620_ProductCatalog/master/TMF620-ProductCatalog-v4.0.0.swagger.json"
    }

    delete_service_1(svc_inv, rfmock, id1, "getsvc")
    

def test_get_unknown_service(svc_inv, rfmock):
    try:
        rfmock.mock_get(f'service/unknown', 'id-unknown', 500)
        _ = svc_inv.get_service("unknown")
        assert false, 'get for "unknown" id did not throw exception'
    except ValueError as e:
        print(f"GET SERVICE expected error: {e}")


def test_list_services(svc_inv, rfmock):
    rfmock.mock_get('service', 'list-all-initial-empty', 200)
    svcs = svc_inv.list_services(state=None)
    print(f"\nLIST ALL SERVICES:\n{json.dumps(svcs, indent=2)}")
    assert svcs == []

    id1 = create_service_1(svc_inv, rfmock, "listsvc")
    
    rfmock.mock_get('service', 'list-svc1', 200)
    svcs = svc_inv.list_services(state=None)
    print(f"\nALL SERVICES:\n{json.dumps(svcs, indent=2)}")
    assert_ids(svcs, [id1])
    assert svcs == [{
      "id": id1,
      "state": "active",
      "componentName": "acme-productinventory",
      "dependencyName": "downstreamproductcatalog",
      "url": "http://components.ihc-dt.cluster-3.de/alice-productcatalogmanagement/tmf-api/productCatalogManagement/v4",
      "OASSpecification": "https://raw.githubusercontent.com/tmforum-apis/TMF620_ProductCatalog/master/TMF620-ProductCatalog-v4.0.0.swagger.json"
    }]

    id2 = create_service_2(svc_inv, rfmock, "listsvc")
    id3 = create_service_3(svc_inv, rfmock, "listsvc")

    rfmock.mock_get('service', 'list-svc123', 200)
    svcs = svc_inv.list_services(state=None)
    print(f"\nALL SERVICES:\n{json.dumps(svcs, indent=2)}")
    assert_ids(svcs, [id1, id2, id3])
    
    rfmock.mock_get('service', 'list-active', 200)
    svcs = svc_inv.list_services()
    print(f"\nactive SERVICES:\n{json.dumps(svcs, indent=2)}")
    assert_ids(svcs, [id1, id3])
    
    rfmock.mock_get('service', 'list-inactive', 200)
    svcs = svc_inv.list_services(state="inactive")
    print(f"\ninactive SERVICES:\n{json.dumps(svcs, indent=2)}")
    assert_ids(svcs, [id2])
    
    rfmock.mock_get('service', 'list-bcme', 200)
    svcs = svc_inv.list_services(component_name="bcme-productinventory", state=None)
    print(f"\nbcme SERVICES:\n{json.dumps(svcs, indent=2)}")
    assert_ids(svcs, [id2, id3])
    
    rfmock.mock_get('service', 'list-downstream', 200)
    svcs = svc_inv.list_services(dependency_name="downstreamproductcatalog", state=None)
    print(f"\ndownstream SERVICES:\n{json.dumps(svcs, indent=2)}")
    assert_ids(svcs, [id1, id2])
    
    rfmock.mock_get('service', 'list-active-bcme', 200)
    svcs = svc_inv.list_services(component_name="bcme-productinventory")
    print(f"\nactive bcme SERVICES:\n{json.dumps(svcs, indent=2)}")
    assert_ids(svcs, [id3])
    
    rfmock.mock_get('service', 'list-active-downstream', 200)
    svcs = svc_inv.list_services(dependency_name="downstreamproductcatalog")
    print(f"\nactive downstream SERVICES:\n{json.dumps(svcs, indent=2)}")
    assert_ids(svcs, [id1])
    
    rfmock.mock_get('service', 'list-active-acme-downstream', 200)
    svcs = svc_inv.list_services(component_name="acme-productinventory", dependency_name="downstreamproductcatalog")
    print(f"\nactive acme downstream SERVICES:\n{json.dumps(svcs, indent=2)}")
    assert_ids(svcs, [id1])
    
    rfmock.mock_get('service', 'list-active-bcme-downstream', 200)
    svcs = svc_inv.list_services(component_name="bcme-productinventory", dependency_name="downstreamproductcatalog")
    print(f"\nactive bcme downstream SERVICES:\n{json.dumps(svcs, indent=2)}")
    assert_ids(svcs, [])
    

    delete_service_1(svc_inv, rfmock, id1, "listsvc")
    delete_service_2(svc_inv, rfmock, id2, "listsvc")
    delete_service_3(svc_inv, rfmock, id3, "listsvc")


def test_update_service(svc_inv, rfmock):
    id2 = create_service_2(svc_inv, rfmock, "updatesvc")
    
    rfmock.mock_get(f'service/{id2}', 'upsv-get-svc2', 200)
    svc2 = svc_inv.get_service(id2)
    print(f"\nGET service-2 BY ID:\n{json.dumps(svc2, indent=2)}")
    assert svc2["state"] == "inactive"
    
    rfmock.mock_patch(f'service/{id2}', 'update-svc2-active', 200)
    svc2b = svc_inv.update_service(
        id=id2,
        componentName=svc2["componentName"], 
        dependencyName=svc2["dependencyName"], 
        url=svc2["url"],
        specification=svc2["OASSpecification"],
        state="active")
    print(f"\nUPDATED service-2 state to active:\n{json.dumps(svc2b,indent=2)}\n")
    assert svc2b == {
      "id": id2,
      "state": "active",
      "componentName": svc2["componentName"],
      "dependencyName": svc2["dependencyName"],
      "url": svc2["url"],
      "OASSpecification": svc2["OASSpecification"]
    }
    
    delete_service_2(svc_inv, rfmock, id2, "listsvc")
    
    try:
        rfmock.mock_patch(f'service/unknown', 'update-unknown', 500)
        svc2b = svc_inv.update_service(
            id="unknown",
            componentName=svc2["componentName"], 
            dependencyName=svc2["dependencyName"], 
            url=svc2["url"],
            specification=svc2["OASSpecification"],
            state="active")
        assert False, "update did not fail for unknown id"
    except ValueError as e:
        assert "Unexpected http status code" in e.args[0]



if __name__ == "__main__":
    #_clean_all()
    pytest.main(["test_service_inventory_client.py", "-s", "-W", "ignore:Module already imported so cannot be rewritten:pytest.PytestAssertRewriteWarning"])
