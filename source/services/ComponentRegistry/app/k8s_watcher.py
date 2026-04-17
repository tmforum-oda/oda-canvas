"""
For more information, see:
- https://kubernetes.io/docs/reference/using-api/api-concepts/#efficient-detection-of-changes
- https://kubernetes.io/docs/reference/using-api/api-concepts/#semantics-for-watch
"""

import os
import time
import asyncio
import datetime
import urllib3
import fnmatch

from typing import List, Optional

from threading import Thread, Lock, Event
from multiprocessing import Process

from kubernetes import config
from kubernetes.client import api_client
from kubernetes.client.exceptions import ApiException
from kubernetes.dynamic.client import DynamicClient


# DEFAULT_NAMESPACES = ["components", "odacompns-*"]  # use None for all namespaces
DEFAULT_NAMESPACES = None
DEFAULT_CALLBACK_DELAY = 10  # seconds


def curr_sec() -> int:
    return int(time.time())

def sec2tim(seconds: int) -> str:
    return datetime.datetime.fromtimestamp(seconds).isoformat()

def sec_age(seconds: int) -> int:
    return curr_sec()-seconds


# Improved version without busy-waiting
class ThreadSafeEventQueue:
    """Thread-safe event queue with efficient waiting using threading.Event."""
    
    # cass variables
    _instance = None
    @classmethod
    def instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
 
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


def init_k8s(proxy=None):  # proxy="http://sia-lb.telekom.de:8080"
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
    

class WatchResourceChangesThread(Thread):

    def __init__(self, dyn_client, queue, api_version, kind, group=None, namespaces:Optional[List[str]]=DEFAULT_NAMESPACES, *args, **kwargs):
        kwargs.setdefault('daemon', True)
        super().__init__(*args, **kwargs)
        self._dyn_client = dyn_client
        self._queue = queue
        self._api_version = api_version
        self._group = group
        self._kind = kind
        self._namespaces = namespaces
        self._search_namespace = None 
        if namespaces is not None and len(namespaces)==1:
            if "*" not in namespaces[0] and "?" not in namespaces[0]:
                self._search_namespace = namespaces[0]
        

    def run(self):
        while True:
            try:
                self.run_inner()
            except Exception as e:
                print(f"Exception in WatchResourceChangesThread for {self._kind}: {e}. Restarting watch...")
                time.sleep(5)
        

    def run_inner(self):
        api = self._dyn_client.resources.get(api_version=self._api_version, group=self._group, kind=self._kind)
        # Setting resource_version=None means the server will send synthetic
        # ADDED events for all resources that exist when the watch starts.
        resource_version = "0"
        while True:
            print(f'Start watching {self._kind} with resource_version "{resource_version}"')
            try:
                for event in api.watch(
                    namespace=self._search_namespace,
                    resource_version=resource_version,
                    allow_watch_bookmarks=True,
                    # timeout=10,
                ):
                    ev_type = event['type']
                    kind = event["raw_object"].get("kind")
                    namespace = event["raw_object"].get("metadata").get("namespace")
                    name = event["raw_object"].get("metadata").get("name")
                    # Remember the last resourceVersion we saw, so we can resume
                    # watching from there if the connection is lost.
                    resource_version = event["raw_object"].get("metadata").get("resourceVersion")
                    if ev_type != "BOOKMARK":
                        if self.check_namespace_match(namespace):
                            print(f"[WATCHER] {ev_type} {kind} {namespace}:{name}: {resource_version}")
                            self._queue.put({"type": ev_type, "kind": kind, "namespace": namespace, "name": name, "resourceVersion": resource_version, "last_update": curr_sec()})
    
            except ApiException as err:
                if err.status == 410:
                    print(f"ERROR: The requested resource version {resource_version} is no longer available.")
                    result = api.get(namespace=self._search_namespace)
                    resource_version = result.metadata.resourceVersion    # resource version of the list query, not the items
                    print(f"list {self._kind} has rv: {resource_version}")
                    for item in result.items:
                        kind = item.kind
                        namespace = item.metadata.namespace
                        name = item.metadata.name
                        rv = item.metadata.resourceVersion
                        if self.check_namespace_match(namespace):
                            print(f"[RESYNC] {kind} {namespace}:{name}: {rv}")
                            self._queue.put({"type": "RESYNC", "kind": kind, "namespace": namespace, "name": name, "resourceVersion": rv, "last_update": curr_sec()})
                else:
                    raise
    
            except urllib3.exceptions.ProtocolError:
                print("Lost connection to the k8s API server. Reconnecting...")
                api = self._dyn_client.resources.get(api_version=self._api_version, group=self._group, kind=self._kind)


    def check_namespace_match(self, namespace: str) -> bool:
        if self._namespaces is None or len(self._namespaces) == 0:
            return True
        for ns_pattern in self._namespaces:
            if fnmatch.fnmatch(namespace, ns_pattern):
                return True
        return False
    


class K8SWatcher:
    
    def __init__(self, callback, callback_delay=DEFAULT_CALLBACK_DELAY):
        self._callback = callback
        self._callback_delay = callback_delay
        self._queue = ThreadSafeEventQueue()
        self._threads = []
        init_k8s()
        self._dyn_client = DynamicClient(api_client.ApiClient())
        self._updated_versions = {}
        self._sent_versions = {}

    def update(self, event):
        ev_type = event['type']
        kind = event['kind']
        namespace = event['namespace']
        name = event['name']
        rv = event['resourceVersion'] if ev_type != "DELETED" else None
        ts = event['last_update']
        self._updated_versions[(kind, namespace, name)] = {"kind": kind, "namespace": namespace, "name": name, "rv": rv, "ts": ts}
        

    def find_oldest_update(self):
        oldest_update = None
        for _, info in self._updated_versions.items():
            ts = info['ts']
            if oldest_update is None or ts < oldest_update['ts']:
                oldest_update = info
        return oldest_update
         
    def add_watch(self, api_version, kind, group=None, namespaces=DEFAULT_NAMESPACES):
        watch_thread = WatchResourceChangesThread(self._dyn_client, self._queue, api_version=api_version, group=group, kind=kind, namespaces=namespaces)
        self._threads.append(watch_thread)
        
        
    def start(self):
        print(f"starting {len(self._threads)} watcher threads")
        for thread in self._threads:
            thread.start()
        print("starting collector for callbacks")
        asyncio.run(self.event_collector())


    async def event_collector(self):
        next_event = None
        while True:
            event = next_event if next_event is not None else self._queue.get()
            next_event = None
            while event is not None:
                self.update(event)
                event = self._queue.get()
            oldest_update = self.find_oldest_update()
            if oldest_update is not None:
                age = sec_age(oldest_update['ts'])
                if age >= self._callback_delay:
                    await self.send_callback(oldest_update)
                else:
                    await asyncio.sleep(self._callback_delay-age)
            else:
                next_event = await self._queue.next()


    async def send_callback(self, info):
        kind = info['kind']
        namespace = info['namespace']
        name = info['name']
        rv = info['rv']
        old_rv = None if (kind, namespace, name) not in self._sent_versions else self._sent_versions[(kind, namespace, name)]["rv"]
        if (rv == old_rv):
            return
        print(f"Sending callback for {kind} {namespace}:{name} with rv {rv} (was {old_rv})")
        try:
            self._sent_versions[(kind, namespace, name)] = info
            del self._updated_versions[(kind, namespace, name)]
            await self._callback(kind, namespace, name, rv, old_rv)
        except Exception as e:
            print(f"Exception in callback for {kind} {namespace}:{name}: {e}")




