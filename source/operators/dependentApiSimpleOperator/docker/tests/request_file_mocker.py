from pathlib import Path
import requests
import requests_mock
import json
import sys
import os

from urllib import parse


def assert_equals(expected, actual):
    assert (
        expected == actual
    ), f"objects not equal:\nEXPECTED: {expected}\nACTUAL:   {actual}"
    return True  #  to allow usage inside another assert condition


class Testdata:
    def __init__(self, base_folder: str, allow_overwrite: bool = False):
        self.base_path = Path(base_folder)
        self.allow_overwrite = allow_overwrite

    def filepath(self, *name_parts: str, ext:str="txt"):
        filtered_name_parts = [
            name_part for name_part in name_parts if name_part is not None
        ]
        filename = "_".join(filtered_name_parts)
        filename = f"{filename}.{ext}"
        return self.base_path / filename

    def write(self, content: str, *name_parts: str, ext:str="txt"):
        path = self.filepath(*name_parts, ext=ext)
        os.makedirs(path.parent, exist_ok=True)
        if not self.allow_overwrite and path.is_file():
            raise ValueError(f"file already exists '{str(path)}'")
        with path.open("w") as f:
            f.write(content)

    def exists(self, *name_parts: str, ext:str="txt"):
        return self.filepath(*name_parts, ext=ext).is_file()

    def exists_json(self, *name_parts: str):
        return self.exists(*name_parts, ext="json")

    def read(self, *name_parts: str, default_result=None, ext:str="txt"):
        path = self.filepath(*name_parts, ext=ext)
        if not path.is_file():
            if default_result is not None:
                return default_result
            raise FileNotFoundError(f"testdata file not found: '{str(path)}'")
        with path.open("r") as f:
            content = f.read()
        return content

    def write_json(self, content_json: dict, *name_parts: str):
        content = json.dumps(content_json, indent=2)
        self.write(content, *name_parts, ext="json")

    def read_json(self, *name_parts: str, default_result=None):
        content = self.read(*name_parts, default_result=default_result, ext="json")
        if isinstance(content, str):
            content = json.loads(content)
        return content


class RequestFileMocker:
    def __init__(
        self,
        mockfiles_folder,
        base_url,
        inital_on=True,
        recording=False,
        allow_overwrite=False,
    ):
        self.testdata = Testdata(mockfiles_folder, allow_overwrite=allow_overwrite)
        self.base_url = base_url
        self.recording = recording
        self.mock_info = {}
        self.mock = requests_mock.Mocker()
        self.is_on = False
        self.url_shortcuts = {}
        if inital_on:
            self.on()

    def add_url_shotcut(self, shortcut, url):
        if not shortcut.startswith("$"):
            raise ValueError("shortcut must start with '$'")
        self.url_shortcuts[shortcut] = url.lower()

    def __del__(self):
        self.off()

    def on(self):
        """
        reactivate mocking
        """
        if not self.is_on:
            self.mock.__enter__()
            self.is_on = True

    def off(self):
        """
        deactivate mocking
        """
        if self.is_on:
            self.mock.__exit__(None, None, None)
            self.is_on = False

    def url(self, path):
        if path == None:
            return requests_mock.ANY
        if path.startswith("$"):
            slash_pos = f"{path}/".find("/")
            shortcut = path[:slash_pos]
            if shortcut not in self.url_shortcuts:
                raise ValueError(f"unknown shortcut '{shortcut}'")
            return path.replace(shortcut, self.url_shortcuts[shortcut])
        return f"{self.base_url}/{path}"

    def extract_path(self, url):
        result = url
        if result == None:
            return None
        if result.lower().startswith(f"{self.base_url.lower()}/"):
            result = result[len(self.base_url) + 1 :]
        else:
            for shortcut, long_url in self.url_shortcuts.items():
                if result.lower().startswith(f"{long_url}/"):
                    result = shortcut+result[len(long_url):]
                    break
            
        qm = result.find("?")
        if qm != -1:
            result = result[:qm]
        return result

    def add_mock_info(self, method, path, name, status_code):
        if self.recording:
            if "*" not in self.mock_info:
                self.mock_info["*"] = [(method, path, name, status_code, 1)]
            else:
                self.mock_info["*"].append((method, path, name, status_code, len(self.mock_info["*"]) + 1))
        else:
            if f"{method}_{path}" not in self.mock_info:
                self.mock_info[f"{method}_{path}"] = [(name, status_code)]
            else:
                self.mock_info[f"{method}_{path}"].append((name, status_code))

    def get_mock_info(self, method, path):
        key = f"{method}_{path}"
        mock_info_list = self.mock_info.get(key, [])
        if len(mock_info_list) == 0:
            return (None, None)
        return mock_info_list.pop(0)

    def mock_post(self, path, name, status_code):
        self.add_mock_info("POST", path, name, status_code)
        if self.recording:
            self.mock.post(requests_mock.ANY, text=self.record_callback)
        else:
            url = self.url(path)
            self.mock.post(url, text=self.text_callback)

    def mock_get(self, path, name, status_code):
        self.add_mock_info("GET", path, name, status_code)
        if self.recording:
            self.mock.get(requests_mock.ANY, text=self.record_callback)
        else:
            url = self.url(path)
            self.mock.get(url, text=self.text_callback)

    def mock_patch(self, path, name, status_code):
        self.add_mock_info("PATCH", path, name, status_code)
        if self.recording:
            self.mock.patch(requests_mock.ANY, text=self.record_callback)
        else:
            url = self.url(path)
            self.mock.patch(url, text=self.text_callback)

    def mock_delete(self, path, name, status_code):
        self.add_mock_info("DELETE", path, name, status_code)
        if self.recording:
            self.mock.delete(requests_mock.ANY, text=self.record_callback)
        else:
            url = self.url(path)
            self.mock.delete(url, text=self.text_callback)

    def text_callback(self, request, context):
        method = request.method
        path = self.extract_path(request.url)
        name, status_code = self.get_mock_info(method, path)
        assert name != None, f"unmocked request for method '{method}' and path '{path}'"

        if method == "POST" or method == "PATCH":
            context.status_code = status_code
            if self.testdata.exists_json(method, name, "payload"):
                expected_payload = self.testdata.read_json(method, name, "payload")
                actual_payload = request.json()
                assert_equals(expected_payload, actual_payload)
            elif self.testdata.exists(method, name, "payload"):
                expected_payload = self.testdata.read(method, name, "payload")
                actual_payload = request.text
                assert_equals(expected_payload, actual_payload)
            response_json = self.testdata.read_json(method, name, "response")
            response = json.dumps(response_json)
            return response
        elif method == "GET" or method == "DELETE":
            qs = parse.parse_qs(parse.urlparse(request.url).query)
            if self.testdata.exists_json(method, name, "params"):
                expected_params = self.testdata.read_json(method, name, "params")
            else:
                expected_params = {}
            assert_equals(expected_params, qs)

            context.status_code = status_code
            response = ""
            if status_code != 204:  # !no data
                response_json = self.testdata.read_json(method, name, "response")
                response = json.dumps(response_json)
            return response
        else:
            raise ValueError("Unsupported method {method} called")

    def record_callback(self, request, context):
        method = request.method
        path = self.extract_path(request.url)
        expected_requests = self.mock_info.get("*",  [])
        assert (
            len(expected_requests) > 0
        ), f"no request expeceted, method: '{method}', path: '{path}'"
        expected_method, expected_path, name, expected_status_code, count = expected_requests.pop(0)
        
        if expected_method == None:
            expected_method = method
        if expected_path == None:
            expected_path = path
        if name == None:
            name = path.replace("/", "-")
        assert_equals(expected_method, method)
        assert_equals(expected_path, path)

        if method == "POST" or method == "PATCH":
            self.off()
            try:
                request_json = requestx.json()
            except Exception:
                request_json = None
            if request_json:
                self.testdata.write_json(request_json, method, name, "payload")
                response = requests.request(method, request.url, json=request_json)
            else:
                request_data = request.text
                if request_data:
                    self.testdata.write(request_data, method, name, "payload")
                response = requests.request(method, request.url, data=request_data, headers=request.headers)
            self.on()

            status_code = response.status_code
            assert expected_status_code is None or assert_equals(
                expected_status_code, status_code
            )

            try:
                response_json = response.json()
                if response_json:
                    self.testdata.write_json(response_json, method, name, "response")
            except Exception:
                pass

            print(
                f"RECORDED: rfmock.mock_{method.lower()}('{path}', '{name}', {status_code})"
            )
            context.status_code = response.status_code
            return response.text

        elif method == "GET" or method == "DELETE":
            # all strings in request.qs are converted to lowercase
            # see https://github.com/jamielennox/requests-mock/issues/264
            qs = parse.parse_qs(parse.urlparse(request.url).query)
            if qs:
                self.testdata.write_json(qs, method, name, "params")

            self.off()
            response = requests.request(method, f"{self.base_url}/{path}", params=qs, headers=request.headers)
            self.on()

            status_code = response.status_code
            assert expected_status_code is None or assert_equals(
                expected_status_code, status_code
            )

            if status_code != 204:  # no content
                response_json = response.json()
                if response_json is not None:
                    self.testdata.write_json(response_json, method, name, "response")

            print(
                f"RECORDED: rfmock.mock_{method.lower()}('{path}', '{name}', {status_code})"
            )
            context.status_code = response.status_code
            return response.text
        else:
            raise ValueError("Unsupported method {method} called")
