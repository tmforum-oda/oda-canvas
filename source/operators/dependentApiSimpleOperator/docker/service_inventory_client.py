import requests
import json



class ServiceInventoryAPI:
    def __init__(self, endpoint):
        self.endpoint = endpoint

    
        
    def list_services(self):
        """
        curl -X 'GET' \
          'https://canvas-info.ihc-dt.cluster-3.de/tmf-api/serviceInventoryManagement/v5/service' \
          -H 'accept: application/json'
        """
        
        url = f"{self.endpoint}/service"
        header = {
            'accept': 'application/json'
        }
        result = requests.get(url, headers=header)    # , auth=HTTPBasicAuth(be_auth_user, be_auth_pw))
        if result.status_code != 200:
            raise ValueError("Unexpected status code {result.status_code}")
        dict_result = json.loads(result.content)
        return dict_result
        


if __name__ == "__main__":
    svc_inv = ServiceInventoryAPI("https://canvas-info.ihc-dt.cluster-3.de/tmf-api/serviceInventoryManagement/v5")
    svcs = svc_inv.list_services()
    for svc in svcs:
        id = svc["id"]
        schars = svc["serviceCharacteristic"]
        dependency_name = [schar["value"] for schar in schars if schar["name"]=="dependencyName"]
        dependency_name = dependency_name[0] if len(dependency_name)>0 else ""
        url = [schar["value"] for schar in schars if schar["name"]=="url"]
        url = url[0] if len(url)>0 else ""
        print(f"ID: {id}, DEPENDENCY: {dependency_name}, URL: {url}")
    
