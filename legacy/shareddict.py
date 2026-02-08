import json
import pickle
from functools import wraps
from contextlib import contextmanager
from multiprocessing import Lock
from multiprocessing.shared_memory import SharedMemory
from typing import (Any, Dict, Generator, ItemsView,
                    Iterator, KeysView, Optional, ValuesView, Final, Protocol)
from shared_memory_dict import SharedMemoryDict
from time import time

NULL_BYTE: Final = b'\x00'

# Lock
# --------------------

class LockType:
    """No Use of Lock"""

    def acquire(self): ...
    
    def release(self): ...

# Serializer
# --------------------

class PickleSer:
    """Pickle Serializer"""

    def dumps(self, obj: dict) -> bytes:
        try:
            return pickle.dumps(obj, pickle.HIGHEST_PROTOCOL)
        except pickle.PicklingError:
            raise SerError(obj)

    def loads(self, bin: bytes) -> dict:
        try:
            return pickle.loads(bin)
        except pickle.UnpicklingError:
            raise DserError(bin)

class JsonSer:
    """JSON Serializer"""

    def dumps(self, obj: dict) -> bytes:
        try:
            return json.dumps(obj).encode() + NULL_BYTE
        except Exception:
            raise SerError(obj)

    def loads(self, bin: bytes) -> dict:
        try:
            return json.loads(bin.split(NULL_BYTE, 1)[0])
        except Exception:
            raise DserError(bin)

class SerType(Protocol):
    """Dummy Serializer for Typing"""
    
    def dumps(self, obj: dict) -> bytes: ...
    
    def loads(self, bin: bytes) -> dict: ...

class SerError(ValueError):
    """Serialization Error"""
    
    def __init__(self, data: dict) -> None:
        super().__init__(f'Failed to serialize data: {data!r}')

class DserError(ValueError):
    """Deserialization Error"""
    
    def __init__(self, data: bytes) -> None:
        super().__init__(f'Failed to deserialize data: {data!r}')

# Shared Dict
# --------------------

class SharedDict:
    """Shared Memory Dictionary"""

    def __init__(self,
                 name: str,
                 create: bool=False,
                 size: int=1024,
                 lock: bool=True,
                 ser: SerType='pickle') -> None:
        super().__init__()
        
        self.name = name
        self.size = size
        
        # Set lock
        if lock:
            self.lock = Lock()
        else:
            self.lock = LockType()
        
        # Set serializer
        if ser == 'pickle':
            self.ser = PickleSer()
        elif ser == 'json':
            self.ser = JsonSer()
        else:
            raise TypeError('Unsupported serializer type')
        
        # Create or connect shared memory
        if create:
            self.shm = self._create(name=self.name, size=self.size)
            is_empty = bytes(self.shm.buf).split(NULL_BYTE, 1)[0] == b''
            if is_empty:
                self.reset()
        else:
            self.shm = self._connect(name=self.name)

    def _lock(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            self.lock.acquire()
            try:
                return func(self, *args, **kwargs)
            finally:
                self.lock.release()
        return wrapper

    @_lock
    def _create(self, name: str, size: int) -> SharedMemory:
        shm = SharedMemory(name=name, create=True, size=size)
        return shm

    def _connect(self, name: str) -> SharedMemory:
        return SharedMemory(name=name)

    def _dumps(self, obj: Dict[str, Any]) -> None:
        bin = self.ser.dumps(obj)
        self.shm.buf[:len(bin)] = bin
        return bin

    def _dumps_for_sure(self, obj: Dict[str, Any]) -> None:
        while True:
            try:
                bin = self._dumps(obj)
                self._loads()
                return bin
            except:
                ...
    
    def _loads(self) -> Dict[str, Any]:
        bin = self.shm.buf.tobytes()
        obj = self.ser.loads(bin)
        return obj
    
    def _load_for_sure(self) -> Dict[str, Any]:
        while True:
            try:
                obj = self._loads()
                return obj
            except:
                ...

    @contextmanager
    @_lock
    def _modify(self) -> Generator:
        shm = self._load_for_sure()
        yield shm
        self._dumps_for_sure(shm)

    def check(self) -> None:
        self._connect(self.name)

    def copy(self) -> dict:
        return self._load_for_sure().copy()

    def keys(self) -> KeysView[Any]:
        return self._load_for_sure().keys()

    def values(self) -> ValuesView[Any]:
        return self._load_for_sure().values()

    def items(self) -> ItemsView:
        return self._load_for_sure().items()

    def get(self, key: str, default: Optional[Any] = None) -> Any:
        return self._load_for_sure().get(key, default)

    def pop(self, key: str, default: Optional[Any] = object()):
        with self._modify() as shm:
            if default is object():
                return shm.pop(key)
            return shm.pop(key, default)

    def update(self, other=(), /, **kwds):
        with self._modify() as shm:
            shm.update(other, **kwds)

    def setdefault(self, key: str, default: Optional[Any] = None):
        with self._modify() as shm:
            return shm.setdefault(key, default)

    @_lock
    def reset(self) -> None:
        self._dumps_for_sure({})

    def close(self) -> None:
        self.shm.close()

    def unlink(self) -> None:
        self.shm.unlink()

    def __getitem__(self, key: str) -> Any:
        return self._load_for_sure()[key]

    def __setitem__(self, key: str, value: Any) -> None:
        with self._modify() as shm:
            shm[key] = value

    def __delitem__(self, key: str) -> None:
        with self._modify() as shm:
            del shm[key]

    def __iter__(self) -> Iterator:
        return iter(self._load_for_sure())

    def __eq__(self, other: Any) -> bool:
        return self._load_for_sure() == other

    def __reversed__(self):
        return reversed(self._load_for_sure())

    def __len__(self) -> int:
        return len(self._load_for_sure())

    def __del__(self) -> None:
        self.close()

    def __contains__(self, key: str) -> bool:
        return key in self._load_for_sure()

    def __ne__(self, other: Any) -> bool:
        return self._load_for_sure() != other

    def __or__(self, other: Any):
        return self._load_for_sure() | other

    def __ror__(self, other: Any):
        return other | self._load_for_sure()

    def __ior__(self, other: Any):
        with self._modify() as shm:
            shm |= other
            return shm

    def __str__(self) -> str:
        return str(self._load_for_sure())

    def __repr__(self) -> str:
        return repr(self._load_for_sure())