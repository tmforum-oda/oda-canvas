import os
import time
from typing import List
import multiprocessing
from multiprocessing import shared_memory


MAX_PROCESSES = 16


class SimpleIPC:

    # Class-level shared resources
    _initialized = False
    _myshl = None 
    _process_id = None
    _process_num = None

    @classmethod
    def init_shm(cls):
        if cls._initialized:
            return
        cls._process_id = os.getpid()
        data = [0] + [0]*MAX_PROCESSES + ['a'*256]*MAX_PROCESSES
        myshl_init = shared_memory.ShareableList(data)
        try:
            myshm = shared_memory.SharedMemory(name="SimpleIPC", create=True, size=myshl_init.shm.size)
            print("CREATED NEW SimpleIPC shared memory")
            for i in range(myshl_init.shm.size):
                myshm.buf[i] = myshl_init.shm.buf[i]
        except FileExistsError:
            print("REUSE EXISTING SimpleIPC shared memory")
            pass
        cls._myshl = shared_memory.ShareableList(name="SimpleIPC")
        cls._initialized = True

    def __init__(self):
        self.init_shm()
        self.register_own_process()
        print(f"Process {self._process_id} registered as process number {self._process_num}")
        
    def register_own_process(self) -> int:
        for i in range(1, MAX_PROCESSES+1):
            if self._myshl[i] == self._process_id:
                self._process_num = i
                return self._process_num
            if self._myshl[i] == 0:
                self._myshl[i] = self._process_id
                time.sleep(0.1)
                return self.register_own_process()
        raise Exception("Maximum number of processes reached")

    def get_data(self, n) -> List:
        return self._myshl[n]

    def inc_data(self, n) -> List:
        result = self._myshl[n] + 1
        self._myshl[n] = result
        return result 

    def get_process_ids(self) -> List[int]:
        result = []
        for i in range(1, MAX_PROCESSES+1):
            if self._myshl[i] != 0:
                result.append(self._myshl[i])
        return result
    
