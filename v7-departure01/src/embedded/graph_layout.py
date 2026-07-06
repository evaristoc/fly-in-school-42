from pathlib import Path
import ctypes

# ── 2. ctypes bindings ───────────────────────────────────────────────────────
BASE = Path(__file__).parent
LIB_OUT = BASE / "libgraph.so"

class CNode(ctypes.Structure):
    _fields_ = [
        ("id",    ctypes.c_int),
        ("label", ctypes.c_char * 32),
        ("x",     ctypes.c_float),
        ("y",     ctypes.c_float),
    ]

lib = ctypes.CDLL(str(LIB_OUT))
lib.compute_layout.argtypes = [ctypes.POINTER(CNode), ctypes.c_int, ctypes.c_float]
lib.compute_layout.restype  = None