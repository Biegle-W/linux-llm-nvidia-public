"""Return freed glibc arenas; never discard live tensor storage."""
import ctypes
class MallInfo(ctypes.Structure):
 _fields_=[(name,ctypes.c_size_t) for name in ['arena','ordblks','smblks','hblks','hblkhd','usmblks','fsmblks','uordblks','fordblks','keepcost']]
lib=ctypes.CDLL(None);lib.mallinfo2.argtypes=[];lib.mallinfo2.restype=MallInfo;lib.malloc_trim.argtypes=[ctypes.c_size_t];lib.malloc_trim.restype=ctypes.c_int

def trim_host_pages(stage,min_free_bytes=64*2**20):
 before=lib.mallinfo2()
 if before.fordblks<min_free_bytes:return None
 trimmed=lib.malloc_trim(0);after=lib.mallinfo2()
 result={'stage':stage,'released':trimmed,'free_arena_before':before.fordblks,'free_arena_after':after.fordblks,'allocated_before':before.uordblks,'allocated_after':after.uordblks}
 print('BOLT_HOST_ALLOCATOR_TRIM',result,flush=True)
 return result
