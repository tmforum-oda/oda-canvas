from jinja2 import (
    Template,
    Environment,
    PackageLoader,
    FileSystemLoader,
    select_autoescape,
)

import requests
import json
import os

from utils import safe_get


class ServiceInventoryAPI:
    def __init__(self, endpoint):
        self.endpoint = endpoint
        template_dir = os.path.join(
            os.path.dirname(os.path.realpath(__file__)), "templates"
        )
        # print(template_dir)
        loader = FileSystemLoader(template_dir)
        self.env = Environment(loader=loader, autoescape=select_autoescape())
        # =======================================================================
        # self.env = Environment(
        #     loader=PackageLoader("service_inventory_client"),
        #     autoescape=select_autoescape()
        # )
        # =======================================================================

    def create_service(self, componentName, dependencyName, url, specification, state):
        """
        curl -X 'POST' \
          'http://localhost:8638/tmf-api/serviceInventoryManagement/v5/service' \
          -H 'accept: application/json' \
          -H 'Content-Type: application/json' \
          -d '{
            "serviceType": "API",
            ...
            }'
        """
        template = self.env.get_template("create-service-payload.json.jinja2")
        payload = template.render(
            componentName=componentName,
            dependencyName=dependencyName,
            url=url,
            specification=specification,
            state=state,
        )
        payload_dict = json.loads(payload)

        url = f"{self.endpoint}/service"
        header = {"accept": "application/json", "Content-Type": "application/json"}
        response = requests.post(url, json=payload_dict, headers=header)
        if response.status_code != 201:
            raise ValueError(
                f"Unexpected http status code {response.status_code} - {response.content.decode()}"
            )

        svc = json.loads(response.content)
        result = self._shorten(svc)
        return result

    def list_services(self, component_name=None, dependency_name=None, state="active"):
        """
        curl -X 'GET' \
          'http://localhost:8638/tmf-api/serviceInventoryManagement/v5/service' \
          -H 'accept: application/json'
        """

        url = f"{self.endpoint}/service"
        header = {"accept": "application/json"}
        params = {}
        if state:
            params["state"] = state
        if component_name:
            params["serviceCharacteristic.value"] = component_name
        elif dependency_name:
            params["serviceCharacteristic.value"] = dependency_name
        response = requests.get(
            url, headers=header, params=params
        )  # , auth=HTTPBasicAuth(be_auth_user, be_auth_pw))
        if response.status_code != 200:
            raise ValueError(f"Unexpected http status code {response.status_code}")
        svc_list = json.loads(response.content)
        result = [self._shorten(svc) for svc in svc_list]
        if component_name:
            result = [
                shortsvc
                for shortsvc in result
                if safe_get(None, shortsvc, "componentName") == component_name
            ]
        if dependency_name:
            result = [
                shortsvc
                for shortsvc in result
                if safe_get(None, shortsvc, "dependencyName") == dependency_name
            ]
        return result

    def get_service(self, id):
        """
        curl -X 'GET' \
          'http://localhost:8638/tmf-api/serviceInventoryManagement/v5/service/5406c1d2-8df8-4e35-bdfc-73548b8bffac' \
          -H 'accept: application/json'
        """
        # TODO[FH]: check format of id
        url = f"{self.endpoint}/service/{id}"
        header = {"accept": "application/json"}
        response = requests.get(url, headers=header)
        if response.status_code != 200:
            raise ValueError(f"Unexpected http status code {response.status_code}")
        svc = json.loads(response.content)
        result = self._shorten(svc)
        return result

    def update_service(
        self, id, componentName, dependencyName, url, specification, state
    ):
        """
        curl -X 'PATCH' \
          'http://localhost:8638/tmf-api/serviceInventoryManagement/v5/service/82beee12-21ab-48fa-9530-dece75c378dc' \
          -H 'accept: application/json' \
          -H 'Content-Type: application/json' \
          -d '{
            "serviceType": "API",
            ...
          }'
        """

        template = self.env.get_template("create-service-payload.json.jinja2")
        payload = template.render(
            componentName=componentName,
            dependencyName=dependencyName,
            url=url,
            specification=specification,
            state=state,
        )
        payload_dict = json.loads(payload)

        url = f"{self.endpoint}/service/{id}"
        header = {"accept": "application/json", "Content-Type": "application/json"}
        response = requests.patch(url, headers=header, json=payload_dict)
        if response.status_code != 200:
            raise ValueError(
                f"Unexpected http status code {response.status_code} - {response.content.decode()}"
            )
        svc = json.loads(response.content)
        result = self._shorten(svc)
        return result

    def delete_service(self, id, ignore_not_found=False) -> bool:
        """
        curl -X 'DELETE' \
          'http://localhost:8638/tmf-api/serviceInventoryManagement/v5/service/5406c1d2-8df8-4e35-bdfc-73548b8bffac' \
          -H 'accept: */*'
        """
        # TODO[FH]: check format of id
        url = f"{self.endpoint}/service/{id}"
        header = {"accept": "*/*"}
        response = requests.delete(url, headers=header)
        if response.status_code == 204:
            return True
        if ignore_not_found:
            return False
        raise ValueError(f"Unexpected http status code {response.status_code}")

    def _shorten(self, svc: dict) -> dict:
        """
        convert this:

        {...
         "id": "5406c1d2-8df8-4e35-bdfc-73548b8bffac"
         "state": "active",
         serviceCharacteristic": [
          {
            "name": "componentName",
            "valueType": "string",
            "value": "acme-productinventory",
            "@type": "StringCharacteristic"
          },
          {
            "name": "dependencyName",
            "valueType": "string",
            "value": "downstreamproductcatalog",
            "@type": "StringCharacteristic"
          },
          ...
        }

        into that:
        {
            "id": "5406c1d2-8df8-4e35-bdfc-73548b8bffac",
            "state": "active",
            "componentName": "acme-productinventory",
            "dependencyName": "downstreamproductcatalog",
            "url": "http://localhost/acme-productcatalogmanagement/tmf-api/productCatalogManagement/v4",
            "OAS Specification": "https://raw.githubusercontent.com/tmforum-apis/TMF620_ProductCatalog/master/TMF620-ProductCatalog-v4.0.0.swagger.json"
         }
        """
        result = {}
        result["id"] = safe_get(None, svc, "id")
        result["state"] = safe_get(None, svc, "state")
        for entry in svc["serviceCharacteristic"]:
            result[entry["name"]] = entry["value"]
        return result
