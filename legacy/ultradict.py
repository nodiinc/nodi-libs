from UltraDict import UltraDict
from os import system
from multiprocessing.shared_memory import SharedMemory

class SharedDict:
    """Shared Memory Dictionary"""
    
    def __init__(self, access_name):
        self.access_name = access_name
    
    def create(self, buffer_size, shared_lock, dump_size):
        
        # Create shared memory
        self.shm = UltraDict(name = self.access_name,
                             create = True,
                             buffer_size = buffer_size,
                             shared_lock = shared_lock,
                             full_dump_size = dump_size,
                             auto_unlink = True)
    
    def connect(self):
        
        # Get shared memory
        self.shm = UltraDict(name = self.access_name,
                             create = False)
    
    def disconnect(self):
        
        # Delete shared memory
        del self.shm
    
    def clear(self):
        
        # Clear POSIX shared memory files
        system('sudo rm /dev/shm/psm* >/dev/null 2>&1')
        
        # Unlink shared memory
        UltraDict.unlink_by_name(name = f'{self.access_name}',
                                 ignore_errors = True)
        UltraDict.unlink_by_name(name = f'{self.access_name}_memory',
                                 ignore_errors = True)
        UltraDict.unlink_by_name(name = f'{self.access_name}_full',
                                 ignore_errors = True)
    
    def check(self):
        
        # Try to connect shared memory, raise exception on failure
        try:
            SharedMemory(name=self.access_name)
        except:
            raise MemoryError
    
    def edge_push_v(self, d: dict, gq: str, gt: str):
        
        # Insert get values, quality, time (only for edge pool)
        for k, v in d.items():
            try:
                tmp = self.shm[k]
                tmp.update({'v': v,
                            'gq': gq,
                            'gt': gt})
                self.shm[k] = tmp
            except:
                self.shm[k] = {'v': v,
                               'gq': gq,
                               'gt': gt,
                               'sq': None,
                               'st': None}
    
    def edge_pull_v(self, d: dict, sq: str, st: str):
        
        # Insert set values, quality, time (only for edge pool)
        for k, v in d.items():
            try:
                tmp = self.shm[k]
                tmp.update({'sq': sq,
                            'st': st})
                self.shm[k] = tmp
            except:
                self.shm[k] = {'v': None,
                               'gq': None,
                               'gt': None,
                               'sq': sq,
                               'st': st}