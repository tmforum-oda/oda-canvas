import multiprocessing
from multiprocessing import shared_memory
import os
import pickle
import threading
import time
from typing import List


APP_NAME = "SimpleIPC"
MAX_PROCESSES = 16
DEFAULT_SHM_SIZE = 1000
MAX_DATA_SIZE = 1000
PROCESS_ALIVE_TIMEOUT = 60  # seconds




class SharedMemoryObject:
    
    _thread_lock = threading.RLock()
    _instances = {}
    
    def __init__(self, name: str, object_creator_function, size: int = DEFAULT_SHM_SIZE):
        with SharedMemoryObject._thread_lock:
            self.name = name
            if name in SharedMemoryObject._instances:
                raise Exception(f"Instance with name {name} already exists")
            try:
                self.shm = shared_memory.SharedMemory(name=name, create=True, size=size+1)
                self.shm.buf[0] = 1  # set pending state
                shared_object = object_creator_function()
                pickled = pickle.dumps(shared_object)
                if len(pickled) > size:
                    raise Exception(f"Data too large ({len(pickled)}/{size}) to serialize {name}")
                self.shm.buf[1:len(pickled)+1] = pickled
                self.shm.buf[0] = 2  # set ready state
            except FileExistsError:
                self.shm = shared_memory.SharedMemory(name=name)
                for i in range(100):
                    if self.shm.buf[0] == 2:
                        break
                    time.sleep(0.1)
                if self.shm.buf[0] != 2:
                    raise Exception(f"Timeout waiting for shared object {name} to be ready")
            SharedMemoryObject._instances[name] = self
                
    def get(self):
        result = pickle.loads(self.shm.buf[1:])
        return result

    @classmethod
    def get_or_create_object(self, name: str, object_creator_function, size: int = DEFAULT_SHM_SIZE):
        with SharedMemoryObject._thread_lock:
            if name in SharedMemoryObject._instances:
                inst = SharedMemoryObject._instances[name]
            else:
                SharedMemoryObject(name, object_creator_function, size)
                inst = SharedMemoryObject._instances[name]
            return inst.get()

    @classmethod
    def close(self):
        with SharedMemoryObject._thread_lock:
            for name, instance in list(SharedMemoryObject._instances.items()):
                instance.shm.close()
            SharedMemoryObject._instances = {}


if __name__ == "__main__":
    # Example usage
    def create_data():
        data = multiprocessing.RLock()
        print(f"Creating data: {data}")
        return data

    mp_lock = SharedMemoryObject.get_or_create_object("shared_memory_object.mp.rlock", create_data)
    print(f"received data {mp_lock}")
    for i in range(10):
        print(f"waiting for lock {i}")
        with mp_lock:
            print(f"got lock {i}")
            for j in range(5):
                time.sleep(1)
        print(f"releasing lock {i}")
    SharedMemoryObject.close()
