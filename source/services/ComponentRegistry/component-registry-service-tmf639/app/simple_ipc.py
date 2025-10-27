import os
import time
import pickle
from typing import List
from multiprocessing import shared_memory


MAX_PROCESSES = 16



def show_buf(data_bytes):
    result = ""
    for b in data_bytes: 
        result = f"{result} {b:02x}"
    print(result)

class SimpleIPC:

    # Class-level shared resources
    _initialized = False
    _myshm = None 
    _myshl = None 
    _process_id = None
    _process_num = None

    @classmethod
    def init_shm(cls):
        if cls._initialized:
            return
        cls._process_id = os.getpid()

        try:
            #     | lock| pid[n]            | last_update[n]    | data[n]               |
            data = [0] + [0]*MAX_PROCESSES + [0]*MAX_PROCESSES + ['a'*256]*MAX_PROCESSES
            myshl_init = shared_memory.ShareableList(data)
            data_bytes = pickle.dumps(myshl_init)
            cls._myshm = shared_memory.SharedMemory(name="SimpleIPC", create=True, size=len(data_bytes))
            print(f"CREATED NEW SimpleIPC shared memory {os.getpid()}")
            cls._myshm.buf[:] = data_bytes[:]
            print(f"COPIED SimpleIPC shared memory {os.getpid()}")
        except FileExistsError:
            print(f"INIT {os.getpid()}")
            cls._myshm = shared_memory.SharedMemory(name="SimpleIPC")
            print(f"REUSE EXISTING SimpleIPC shared memory {os.getpid()}")
            time.sleep(0.25)
            
        while True:
            try:
                cls._myshl = pickle.loads(cls._myshm.buf)
                if (not isinstance(cls._myshl, shared_memory.ShareableList)):
                    raise ValueError("wrong depickled")
                break
            except:
                time.sleep(0.25)
                pass
        cls._initialized = True

    def get_shm_lock(self) -> int:
        return self._myshl[0]
    def get_shm_pid(self, n:int) -> int:
        return self._myshl[n]
    def get_shm_lastupdate(self, n:int) -> int:
        return self._myshl[MAX_PROCESSES + n]
    def get_shm_data(self, n:int) -> str:
        return self._myshl[2*MAX_PROCESSES + n]
    def set_shm_lock(self, value:int):
        self._myshl[0] = value
    def set_shm_pid(self, n:int, value:int):
        self._myshl[n] = value
    def set_shm_lastupdate(self, n:int, value:int):
        self._myshl[MAX_PROCESSES + n] = value
    def set_shm_data(self, n:int, value:str):
        self._myshl[2*MAX_PROCESSES + n] = value

    def alive(self):
        if self.get_shm_pid(self._process_num) != self._process_id:
            self.register_own_process()
        self.set_shm_lastupdate(self._process_num, int(time.time()))
    def cleanup(self):
        expired = int(time.time()) - 60  # 1 minute expiration
        for i in range(1, MAX_PROCESSES+1):
            if self.get_shm_pid(i) != 0 and self.get_shm_lastupdate(i) < expired:
                self.set_shm_pid(i, 0)
                self.set_shm_lastupdate(i, 0)
                self.set_shm_data(i, 'a'*256)


    def __init__(self, delayed_init: bool = False):
        if not delayed_init:
            self.init()

    def init(self):
        self.init_shm()
        self.register_own_process()
        print(f"Process {self._process_id} registered as process number {self._process_num}")


    def leader_election(self) -> int:
        procs = self.get_process_ids()
        if not procs:
            return self._process_id
        result = min(procs)
        return result

    def is_leader(self) -> bool:
        return self.leader_election() == self._process_id
    
    def register_own_process(self) -> int:
        for i in range(1, MAX_PROCESSES+1):
            try:
                if self.get_shm_pid(i) == self._process_id:
                    self._process_num = i
                    return self._process_num
            except ValueError as e:
                print(f"ERROR {e} at index {i} in {os.getpid()}")
                time.sleep(0.1)
        for i in range(1, MAX_PROCESSES+1):
            if self.get_shm_pid(i) == 0:
                self.set_shm_pid(i, self._process_id)
                self.set_shm_lastupdate(i, int(time.time()))
                time.sleep(0.1)
                return self.register_own_process()
        raise Exception("Maximum number of processes reached")

    def get_process_ids(self) -> List[int]:
        result = []
        for i in range(1, MAX_PROCESSES+1):
            if self.get_shm_pid(i) != 0:
                result.append(self.get_shm_pid(i))
        return result
    
    def shutdown(self):
        if self._process_num is not None:
            self.set_shm_pid(self._process_num, 0)
            self.set_shm_lastupdate(self._process_num, 0)
            self.set_shm_data(self._process_num, 'a'*256)
            print(f"Process {self._process_id} unregistered from process number {self._process_num}")
            self._process_num = None
