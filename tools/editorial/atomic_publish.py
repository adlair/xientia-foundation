"""Linux atomic directory publish without overwriting an existing destination."""
import ctypes
import errno
import os
from pathlib import Path

AT_FDCWD = -100
RENAME_NOREPLACE = 1

def publish_noreplace(source, destination):
    source, destination = Path(source), Path(destination)
    libc = ctypes.CDLL(None, use_errno=True)
    func = libc.renameat2
    func.argtypes = [ctypes.c_int, ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p, ctypes.c_uint]
    func.restype = ctypes.c_int
    result = func(AT_FDCWD, os.fsencode(source), AT_FDCWD, os.fsencode(destination), RENAME_NOREPLACE)
    if result != 0:
        error = ctypes.get_errno()
        raise OSError(error, os.strerror(error), str(destination))
