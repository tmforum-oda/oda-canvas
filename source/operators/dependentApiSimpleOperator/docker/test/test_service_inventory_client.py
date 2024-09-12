import sys
import os

try:
    import service_inventory_client
except ModuleNotFoundError:
    # allow running component locally without setting PYTHONPATH
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')))
    import service_inventory_client

import requests
import requests_mock

from service_inventory_client import ServiceInventoryAPI
import json



def test_service_inventory_api():
    svc_inv = ServiceInventoryAPI("https://canvas-info.ihc-dt.cluster-3.de/tmf-api/serviceInventoryManagement/v5")
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

    #id = 'b3d325e5-40e9-41cf-a333-1473750f4a7e'
    id = 'xxx'
    url = f'https://canvas-info.ihc-dt.cluster-3.de/tmf-api/serviceInventoryManagement/v5/service/{id}'
    response = '{"serviceType":"API","name":"Acme partner catalog","description":"Implementation of TMF620 Product Catalog Management Open API","state":"active","serviceCharacteristic":[{"name":"componentName","valueType":"string","value":"acme-productinventory","@type":"StringCharacteristic"},{"name":"dependencyName","valueType":"string","value":"downstreamproductcatalog","@type":"StringCharacteristic"},{"name":"url","valueType":"string","value":"http://localhost/acme-productcatalogmanagement/tmf-api/productCatalogManagement/v4","@type":"StringCharacteristic"},{"name":"OAS Specification","valueType":"string","value":"https://raw.githubusercontent.com/tmforum-apis/TMF620_ProductCatalog/master/TMF620-ProductCatalog-v4.0.0.swagger.json","@type":"StringCharacteristic"}],"serviceSpecification":{"id":"1","name":"API","version":"1.0.0","@type":"ServiceSpecification","specCharacteristic":[{"name":"componentName","valueType":"string","description":"The name of the component which wants to consume the API service. The component name is normally available in the environment vaiable COMPONENT_NAME","@type":"StringCharacteristic"},{"name":"dependencyName","valueType":"string","description":"The dependency name that this API service matches. The dependency name is set in the Component Specification","@type":"StringCharacteristic"},{"name":"url","valueType":"string","description":"The url the the API root endpoint","@type":"StringCharacteristic"},{"name":"OAS Specification","valueType":"string","description":"The url to the Open API Speciofication for this API","@type":"StringCharacteristic"}]},"@type":"Service","id":"b3d325e5-40e9-41cf-a333-1473750f4a7e","href":"http://canvas-info.ihc-dt.cluster-3.de/tmf-api/serviceInventoryManagement/v5/service/b3d325e5-40e9-41cf-a333-1473750f4a7e","@schemaLocation":"http://localhost:8080/openapi#/components.schemas.Service","@baseType":"Service"}'

    with requests_mock.Mocker() as m:
        m.get(url, text=response)
        
        svc = svc_inv.get_service(id)
        print(f"\nFOUND active acme-productinventory.downstreamproductcatalog SERVICES:\n{json.dumps(svc, indent=2)}\n")

    return
  

    svc = svc_inv.create_service(
        componentName="alice-pc-consumer", 
        dependencyName="upstreamproductcatalog6", 
        url="http://components.ihc-dt.cluster-3.de/alice-productcatalogmanagement/tmf-api/productCatalogManagement/v4",
        specification="https://raw.githubusercontent.com/tmforum-apis/TMF620_ProductCatalog/master/TMF620-ProductCatalog-v4.0.0.swagger.json",
        state="inactive")
    print(f"\nCREATED SERVICE:\n{json.dumps(svc,indent=2)}\n")
 
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