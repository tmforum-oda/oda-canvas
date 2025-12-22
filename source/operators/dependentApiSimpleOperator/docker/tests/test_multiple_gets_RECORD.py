import pytest
import sys
import os
import time
import requests


from request_file_mocker import RequestFileMocker

import json


## for local tests to the cluster use:
## kubectl port-forward -n canvas svc/canvas-compreg 8080:80
BASE_URL = "https://api.restful-api.dev"
RM_TESTDATA_FOLDER = "testdata/requests_multiple_gets_mock"

INSTANCES = {}


@pytest.fixture
def rfmock() -> RequestFileMocker:
    if "rfm" not in INSTANCES:
        INSTANCES["rfm"] = RequestFileMocker(f"{RM_TESTDATA_FOLDER}-temp", BASE_URL, recording=True, allow_overwrite=True)
        # INSTANCES["rfm"] = RequestFileMocker(RM_TESTDATA_FOLDER, BASE_URL)
    return INSTANCES["rfm"]



def get_time(url):
    response = requests.get(url)
    response.raise_for_status()
    return response.content

def test_get(rfmock):
    rfmock.mock_get("objects/7", f"Objekt 7", 200)
    content1 = get_time(f"{BASE_URL}/objects/7")
    print(f"\nGOT CONTENT:\n{content1}\n")
    time.sleep(2)
    rfmock.mock_get("objects/6", f"Objekt 6", 200)
    content2 = get_time(f"{BASE_URL}/objects/6")
    print(f"\nGOT CONTENT:\n{content2}\n")
    assert content1 != content2
    


if __name__ == "__main__":
    # _clean_all()
    pytest.main(
        [
            "test_multiple_gets.py",
            "-s",
            "-W",
            "ignore:Module already imported so cannot be rewritten:pytest.PytestAssertRewriteWarning",
        ]
    )
