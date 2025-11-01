import os
import time
from multiprocessing import shared_memory


class GlobalLock:
    _name = None
    _shm = None

    def __init__(self, name: str) -> bool:
        self._name = name
        self._shm = None

    def __enter__(self):
        self.acquire_lock()

    def __exit__(self, exc_type, exc, exc_tb):
        self.release_lock()

    def acquire_lock(self, timeout=0) -> bool:
        start_time = time.time()
        while True:
            try:
                self._shm = shared_memory.SharedMemory(name=self._name, create=True, size=256)
                print(f"ACQUIRED LOCK {self._name}")
                return True
            except FileExistsError:
                print(f"LOCK {self._name} IS HELD BY ANOTHER PROCESS")
                if timeout > 0 and (time.time() - start_time) >= timeout:
                    print(f"TIMEOUT WHILE WAITING FOR LOCK {self._name}")
                    return False
                time.sleep(0.1)
    
    def release_lock(self):
        if self._shm is None:
            raise RuntimeError("Lock not acquired or already released")
        else:
            self._shm.close()
            self._shm.unlink()
            self._shm = None
            print(f"RELEASED LOCK {self._name}")
            
    def is_locked(self) -> bool:
        try:
            shm = shared_memory.SharedMemory(name=self._name)
            shm.close()
            return True
        except FileNotFoundError:
            return False

    def close(self):
        if self._shm is not None:
            self.release_lock()

if __name__ == "__main__":
    lock = GlobalLock("global_lock_example")
    
    with lock:
        print("Doing work while holding the lock...")
        input("Press Enter to release the lock and exit...")
