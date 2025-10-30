# from https://github.com/kubernetes-client/python/blob/master/examples/watch/watch_recovery.py

# Copyright 2025 The Kubernetes Authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Uses watch to print a stream of Pod events from the default namespace.
The allow_watch_bookmarks flag is set to True, so the API server can send
BOOKMARK events.

If the connection to the API server is lost, the script will reconnect and 
resume watching from the most recently received resource version.

For more information, see:
- https://kubernetes.io/docs/reference/using-api/api-concepts/#efficient-detection-of-changes
- https://kubernetes.io/docs/reference/using-api/api-concepts/#semantics-for-watch
"""

import os
import time
import json
import datetime
import asyncio
import urllib3

from kubernetes import config, watch, client
from kubernetes.client import api_client
from kubernetes.client.exceptions import ApiException
from kubernetes.dynamic.client import DynamicClient

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from threading import Thread, Lock, Event

#NAMESPACE = "canvas"
NAMESPACE = "components"



# Improved version without busy-waiting
class ThreadSafeEventQueue:
    """Thread-safe event queue with efficient waiting using threading.Event."""
    
    def __init__(self):
        self.lock = Lock()
        self.queue = []
        self.event = Event()
    
    def put(self, event):
        """Add an event to the queue and signal waiting threads."""
        with self.lock:
            self.queue.append(event)
            self.event.set()  # Signal that data is available
    
    def get(self):
        """Get an event from the queue if available."""
        with self.lock:
            result = self.queue.pop(0) if self.queue else None
            if not self.queue:
                self.event.clear()  # Clear event if queue is empty
            return result
    
    async def next(self):
        """
        Wait for and return the next event without busy-waiting.
        Uses threading.Event to efficiently wait for new data.
        """
        result = self.get()
        while result is None:
            # Wait for event to be set (blocking but non-CPU-intensive)
            # run_in_executor allows us to wait on the threading.Event without blocking the asyncio loop
            await asyncio.get_event_loop().run_in_executor(None, self.event.wait)
            result = self.get()
        return result


scheduler = AsyncIOScheduler()
queue = ThreadSafeEventQueue()


def init_k8s(proxy=None):
    try:
        # Try to load in-cluster config first, then kubeconfig
        try:
            config.load_incluster_config()
            print("Using in-cluster Kubernetes configuration")
        except config.ConfigException:
            config.load_kube_config()
            print("Using kubeconfig for Kubernetes configuration")
        k8s_proxy = os.getenv('K8S_PROXY', proxy)
        if k8s_proxy:
            api_client.Configuration._default.proxy = k8s_proxy
            print(f"set proxy to {k8s_proxy}")
        
    except Exception as e:
        print(f"Failed to configure Kubernetes client: {e}")
        raise
    

class ComponentsConsumerThread(Thread):

    def __init__(self, client, queue, *args, **kwargs):
        kwargs.setdefault('daemon', True)
        super().__init__(*args, **kwargs)
        self.client = client
        self.queue = queue

    def run(self):
        api = self.client.resources.get(api_version="v1", group="oda.tmforum.org", kind="Component")
        # Setting resource_version=None means the server will send synthetic
        # ADDED events for all resources that exist when the watch starts.
        resource_version = ""
        while True:
            print("Starting component watch with resource_version=%s" % resource_version)
            try:
                for event in api.watch(
                    namespace=NAMESPACE,
                    resource_version=resource_version,
                    allow_watch_bookmarks=True,
                    timeout=10,
                ):
                    # Remember the last resourceVersion we saw, so we can resume
                    # watching from there if the connection is lost.
                    resource_version = event['object'].metadata.resourceVersion
    
                    print("  Event: %s %s %s %s" % (
                        resource_version,
                        event['type'],
                        event['object'].kind,
                        event['object'].metadata.name,
                    ))
                    if event['type'] != "BOOKMARK":
                        self.queue.put(event)
    
            except ApiException as err:
                if err.status == 410:
                    print("ERROR: The requested resource version is no longer available.")
                    resource_version = ""
                else:
                    raise
    
            except urllib3.exceptions.ProtocolError:
                print("Lost connection to the k8s API server. Reconnecting...")


class PodsWatcher:

    def __init__(self, *args, **kwargs):
        self._v1_api = client.CoreV1Api()
        self._resource_version = "0"
        self._old_rv = ""
        self._pod_changes = {}
        self._pod_versions = {}

    def updatePODchanges(self, namespace=NAMESPACE):

        rvstr = datetime.datetime.fromtimestamp(int(self._resource_version)//1000000000).isoformat() if self._resource_version else "''"
        print(f"query pod changes since resource_version={self._resource_version} {rvstr}")

        #=======================================================================
        # else:
        #     # result = self._v1_api.list_namespaced_pod(namespace, resource_version=self._resource_version, resource_version_match="NotOlderThan")
        #     result = self._v1_api.list_namespaced_pod(namespace, resource_version=self._resource_version, resource_version_match="Exact")
        #     # result = self._v1_api.list_namespaced_pod(namespace, resource_version=self._resource_version)
        #     print(result.metadata.resource_version)
        #     print(result.items[0].metadata.resource_version)
        #     print(result.items[1].metadata.resource_version)
        #     self._resource_version = result.metadata.resource_version
        #     #self._resource_version = result.items[0].metadata.resource_version
        #     #self._resource_version = result.items[1].metadata.resource_version
        #=======================================================================
            
        try:
            watcher = watch.Watch()
 
            for event in watcher.stream(
                self._v1_api.list_namespaced_pod, namespace,
                resource_version=self._resource_version,
                allow_watch_bookmarks=True,
                timeout_seconds=1,
                limit=1,
            ):
                ev_type = event['type']
                rv = event["raw_object"].get("metadata").get("resourceVersion")
                name = event["raw_object"].get("metadata").get("name")
                dt = datetime.datetime.fromtimestamp(int(rv)//1000000000)
                dt_str = dt.isoformat()
                print(f"Event {dt_str} rv={rv} {ev_type}: {name}")
                # self._resource_version = max(self._resource_version, rv)
                self._resource_version = rv
                if self._pod_versions.get(name, None) != rv:
                    self._pod_versions[name] = rv
                    self._pod_changes[name] = rv
                
 
        except ApiException as err:
            if err.status == 410:
                print("ERROR: The requested resource version is no longer available.")
                # https://kubernetes.io/docs/reference/using-api/api-concepts/#efficient-detection-of-changes
                result = self._v1_api.list_namespaced_pod(namespace)
                self._resource_version = result.metadata.resource_version
                print(f"list pods rv: {self._resource_version}")
                
                for item in result.items:
                    name = item.metadata.name
                    rv = item.metadata.resource_version
                    dt = datetime.datetime.fromtimestamp(int(rv)//1000000000)
                    dt_str = dt.isoformat()
                    if self._pod_versions.get(name, None) != rv:
                        print(f"  Pod {dt_str} rv={rv}: {name}")
                        self._pod_versions[name] = rv
                        self._pod_changes[name] = rv
            else:
                raise
 
        except urllib3.exceptions.ProtocolError:
            print("Lost connection to the k8s API server. Reconnecting...")
            self._v1_api = client.CoreV1Api()


    def getChanges(self):
        changes = self._pod_changes
        self._pod_changes = {}
        return changes



async def show_events(queue:ThreadSafeEventQueue, num_events:int):
    for _ in range(num_events):
        event = await queue.next()
        print("[SHOW] rcv: %s %s %s" % (
            event['type'],
            event['object'].kind,
            event['object'].metadata.name,
        ))
        #print(json.dumps(event["raw_object"], indent=2))

    def run(self):
        api = self.client.resources.get(api_version="v1", kind="Pod")
        # Setting resource_version=None means the server will send synthetic
        # ADDED events for all resources that exist when the watch starts.
        resource_version = ""
        while True:
            print("Starting pod watch with resource_version=%s" % resource_version)
            try:
                for event in api.watch(
                    namespace=NAMESPACE,
                    resource_version=resource_version,
                    allow_watch_bookmarks=True,
                    timeout=10,
                ):
                    # Remember the last resourceVersion we saw, so we can resume
                    # watching from there if the connection is lost.
                    resource_version = event['object'].metadata.resourceVersion
    
                    print("  Event: %s %s %s %s" % (
                        resource_version,
                        event['type'],
                        event['object'].kind,
                        event['object'].metadata.name,
                    ))
                    if event['type'] != "BOOKMARK" or True:
                        self.queue.put(event)
    
            except ApiException as err:
                if err.status == 410:
                    print("ERROR: The requested resource version is no longer available.")
                    resource_version = ""
                else:
                    raise
    
            except urllib3.exceptions.ProtocolError:
                print("Lost connection to the k8s API server. Reconnecting...")



# see https://www.nashruddinamin.com/blog/running-scheduled-jobs-in-fastapi
@scheduler.scheduled_job('interval', seconds=10)  # ('cron', hour=13, minute=05)
async def process_events():
    print("Fetching current time...")
    

def main():
    # Configs can be set in Configuration class directly or using helper
    # utility. If no argument provided, the config will be loaded from
    # default location.
    init_k8s("http://sia-lb.telekom.de:8080")
    #init_k8s()

    pods_watcher = PodsWatcher()

    for i in range(10):
        print(f"Updating pod changes iteration {i}")
        pods_watcher.updatePODchanges("canvas")  # ("canvas")
        print(f"Pod changes: {pods_watcher.getChanges()}")
        asyncio.run(asyncio.sleep(2))
    
    print("Main thread finished")
    


if __name__ == "__main__":
    main()
