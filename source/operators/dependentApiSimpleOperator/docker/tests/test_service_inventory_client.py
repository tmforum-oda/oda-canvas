import sys
import os

try:
    import service_inventory_client
except ModuleNotFoundError:
    # allow running component locally without setting PYTHONPATH
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '../src')))
    import service_inventory_client

import requests
import requests_mock

from service_inventory_client import ServiceInventoryAPI
import json


BASE_URL="https://canvas-info.ihc-dt.cluster-3.de/tmf-api/serviceInventoryManagement/v5"

def assert_equals(expected, actual):
    if expected != actual:
        print(f"objects not equal:\nEXPECTED: {expected}\nACTUAL:   {actual}")
    assert expected == actual
    
def testdata(filename:str, default_result = None):
    td_filename = f"testdata/{filename}" 
    if not os.path.isfile(td_filename):
        if default_result is not None:
            return default_result
        raise FileNotFoundError(f"testdata file not found: '{td_filename}'")
    with open(td_filename, "r") as f:
        text = f.read()
    return text

def write_testdata(filename:str, content:str):
    td_filename = f"testdata/{filename}" 
    with open(td_filename, "w") as f:
        f.write(content)

def writejson_testdata(filename:str, content:dict):
    write_testdata(filename, json.dumps(content, indent=2))


class PostMock:
    def __init__(self, payload, status_code, response_text):
        self.payload = payload
        self.status_code = status_code
        self.response_text = response_text
        
    def text_callback(self, request, context):
        print(request)
        context.status_code = self.status_code
        return self.response_text

class RecordMock:
    def __init__(self):
        self.method = None
        self.name = None

    def record_next(self, method, path, name, status_code):
        assert self.method is None
        self.method = method
        self.path = path
        self.status_code = status_code
        self.name = name
        
    def record_trace(self, frame, event, arg):
        if event == 'call':
            return self.record_trace
        if event != 'return':
            return
        if frame.f_code.co_name != self.method:
            return
        if self.method == "post":
            if str(frame.f_code.co_varnames) == "('url', 'data', 'json', 'kwargs')":
                params = frame.f_locals
                print(params)
                response = arg
                url = params["url"] if "url" in params else None
                assert url.startswith(f"{BASE_URL}/")
                path = url.replace(f"{BASE_URL}/", "")
                assert self.path is None or self.path == path
                data_json = params["json"] if "json" in params else None
                if not data_json:
                    data = params["data"] if "data" in params else None
                    if data:
                        data_json = json.loads(data)
                status_code = response.status_code
                assert self.path is None or self.path == path
                response_json = response.json()
                if data_json:
                    payload_filename= f"requests_mock/post_payload_{self.name}.json"
                    writejson_testdata(payload_filename, data_json)
                if response_json:
                    response_filename= f"requests_mock/post_response_{self.name}.json"
                    writejson_testdata(response_filename, response_json)
                print(f"RECORDED: mock_post(m, '{path}', '{self.name}', {status_code}")
                self.method = None
                        

def mock_get(m, path, name):
    url = f"{BASE_URL}/{path}"
    filename = f"requests_mock/get_response_{name}.json"
    print(f"mocking GET {url} from {filename}")
    text = testdata(filename)
    m.get(url, text=text)

def mock_post(m, path, name, status_code=200):
    url = f"{BASE_URL}/{path}"
    filename_payload = f"requests_mock/post_payload_{name}.json"
    filename_response = f"requests_mock/post_response_{name}.json"
    print(f"mocking POST {url} from {filename_response}")
    payload = testdata(filename_payload)
    response = testdata(filename_response)
    pm = PostMock(payload, status_code, response)
    m.post(url, text=pm.text_callback)

def record_post(m, path, name, rqs):
    url = f"{BASE_URL}/{path}"
    print(f"OUTER: '{url}'")

    filename_payload = f"requests_mock/post_payload_{name}.json"
    filename_response = f"requests_mock/post_response_{name}.json"
    print(f"recording POST {url} from {filename_response}")
    rm = RecordMock(filename_payload, filename_response, rqs)
    m.post(url, text=rm.record_callback)


# from https://discuss.python.org/t/interception-of-methods-from-python-modules-compiled-into-the-interpreter/6215/3
# https://elizaveta239.github.io/the-hidden-power-part1/
def tracer(frame, event, arg):
    if event == 'call':
        if frame.f_code.co_name == "post":
            if str(frame.f_code.co_varnames) == "('url', 'data', 'json', 'kwargs')":
                # frame.f_code.co_filename.endswith("requests\api.py")
                params = frame.f_locals
                url = params["url"] if "url" in params else None
                data = params["data"] if "data" in params else None
                print(f"post({url})")
                if data:
                    print("\nDATA:\n-----------\n{data}\n-------------\n")
        return tracer
    elif event == 'return':
        if frame.f_code.co_name == "post":
            if str(frame.f_code.co_varnames) == "('url', 'data', 'json', 'kwargs')":
                print(arg)
                print(frame.f_locals)

def post(url):
    return "OK"

def test_service_inventory_api():
    svc_inv = ServiceInventoryAPI(BASE_URL)
    #===========================================================================
    # svcs = svc_inv.list_services()
    # print(f"SERVICES FOR *.*\n{json.dumps(svcs, indent=2)}")
    # svcs = svc_inv.list_services(component_name="bcme-productinventory")
    # print(f"SERVICES FOR bcme-productinventory.*\n{json.dumps(svcs, indent=2)}")
    # svcs = svc_inv.list_services(dependency_name="downstreamproductcatalog")
    # print(f"SERVICES FOR *.downstreamproductcatalog\n{json.dumps(svcs, indent=2)}")
    # svcs = svc_inv.list_services(component_name="bcme-productinventory", dependency_name="downstreamproductcatalog")
    # print(f"SERVICES FOR COMPONENT bcme-productinventory.downstreamproductcatalog\n{json.dumps(svcs, indent=2)}")
    # svcs = svc_inv.list_services(component_name="bcme-productinventory", dependency_name="x")
    # print(f"SERVICES FOR COMPONENT bcme-productinventory.x\n{json.dumps(svcs, indent=2)}")
    # svcs = svc_inv.list_services(component_name="x", dependency_name="downstreamproductcatalog")
    # print(f"SERVICES FOR COMPONENT x.downstreamproductcatalog\n{json.dumps(svcs, indent=2)}")
    #===========================================================================

    rm = RecordMock()

    #with requests_mock.Mocker() as m:
    if True:
        
        #mock_post(m, "service", "create", 201)
        sys.setprofile(rm.record_trace)

        rm.record_next("post", None, "create", None)
        svc = svc_inv.create_service(
            componentName="alice-pc-consumer", 
            dependencyName="downstreamproductcatalog", 
            url="http://components.ihc-dt.cluster-3.de/alice-productcatalogmanagement/tmf-api/productCatalogManagement/v4",
            specification="https://raw.githubusercontent.com/tmforum-apis/TMF620_ProductCatalog/master/TMF620-ProductCatalog-v4.0.0.swagger.json",
            state="inactive")
        print(f"\nCREATED SERVICE:\n{json.dumps(svc,indent=2)}\n")

        sys.setprofile(None)

        return
        record_next(self, method, name)        
        assert_equals(svc, {
          "id": "7e57da7a-123",
          "state": "inactive",
          "componentName": "alice-pc-consumer",
          "dependencyName": "downstreamproductcatalog",
          "url": "http://components.ihc-dt.cluster-3.de/alice-productcatalogmanagement/tmf-api/productCatalogManagement/v4",
          "OAS Specification": "https://raw.githubusercontent.com/tmforum-apis/TMF620_ProductCatalog/master/TMF620-ProductCatalog-v4.0.0.swagger.json"
        })

        return 
    
        id = svc["id"]
        mock_get(m, f"service/{id}", f"id_{id}")
        
        svc = svc_inv.get_service(id)
        print(f"\nFOUND active acme-productinventory.downstreamproductcatalog SERVICES:\n{json.dumps(svc, indent=2)}\n")

        assert_equals(svc, {
          "id": "7e57da7a-123",
          "state": "active",
          "componentName": "acme-productinventory",
          "dependencyName": "downstreamproductcatalog",
          "url": "http://localhost/acme-productcatalogmanagement/tmf-api/productCatalogManagement/v4",
          "OAS Specification": "https://raw.githubusercontent.com/tmforum-apis/TMF620_ProductCatalog/master/TMF620-ProductCatalog-v4.0.0.swagger.json"
        })

    return
  

    svc_list = svc_inv.list_services(svc["componentName"], svc["dependencyName"], state=svc["state"])
    print(f"\nFOUND inactive SERVICES:\n{json.dumps(svc_list,indent=2)}\n")

    svc_list = svc_inv.list_services(svc["componentName"], svc["dependencyName"])
    print(f"\nFOUND active SERVICES:\n{json.dumps(svc_list,indent=2)}\n")

    svc2 = svc_inv.update_service(
        id=svc["id"],
        componentName=svc["componentName"], 
        dependencyName=svc["dependencyName"], 
        url=svc["url"],
        specification=svc["OASSpecification"],
        state="active")
    print(f"\nUPDATED SERVICE STATE:\n{json.dumps(svc2,indent=2)}\n")

    svc_list = svc_inv.list_services(svc["componentName"], svc["dependencyName"])
    print(f"\nFOUND active SERVICES:\n{json.dumps(svc_list,indent=2)}\n")

    svc4 = svc_inv.get_service(svc["id"])
    print(f"SERVICE by id\n{json.dumps(svc4,indent=2)}")
    
    svc_inv.delete_service(svc["id"])
    print(f'DELETED SERVICE {svc["id"]}')

    try:
        svc4 = svc_inv.get_service(svc["id"])
        raise Exception(f'GET AFTER DELETE WAS SUCCESSFUL FOR {svc["id"]}')
    except ValueError as e:
        print(f"GET SERVICE expected error: {e}")



if __name__ == "__main__":
    test_service_inventory_api()