import importlib.util,mmap,tempfile,unittest,os
from pathlib import Path
spec=importlib.util.spec_from_file_location('cache_fix',Path(__file__).resolve().parents[1]/'scripts/bolt_offload_hook/checkpoint_cache.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
def write(path,data):
 path.write_bytes(data)
 with path.open('rb') as f:os.fsync(f.fileno())
class ReadOnlyCache(unittest.TestCase):
 def test_readonly_mapping_refaults_original_bytes_without_file_change(self):
  with tempfile.TemporaryDirectory(prefix='cache test ',dir=Path(__file__).parent) as d:
   p=Path(d)/'weights';data=bytes(range(256))*32;write(p,data)
   with p.open('rb') as f,mmap.mmap(f.fileno(),0,access=mmap.ACCESS_READ) as view:
    self.assertEqual(view[:],data);r=m.release_clean_mappings(p);self.assertGreaterEqual(r['mappings'],1);self.assertEqual(view[:],data)
   self.assertEqual(p.read_bytes(),data)
 def test_writable_private_tensor_and_unrelated_mapping_preserved(self):
  with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as d:
   p=Path(d)/'weights';write(p,b'a'*8192);other=Path(d)/'other';write(other,b'b'*8192)
   with p.open('rb') as f,other.open('rb') as g,mmap.mmap(f.fileno(),0,access=mmap.ACCESS_COPY) as live,mmap.mmap(g.fileno(),0,access=mmap.ACCESS_READ) as unrelated:
    live[0]=122;r=m.release_clean_mappings(p);self.assertEqual(r['mappings'],0);self.assertEqual(live[0],122);self.assertEqual(unrelated[:],b'b'*8192)
   self.assertEqual(p.read_bytes(),b'a'*8192)
class CleanPrivate(unittest.TestCase):
 def test_unmodified_private_file_mapping_refaults_same_data(self):
  with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as d:
   p=Path(d)/'weights';write(p,b'q'*8192)
   with p.open('rb') as f,mmap.mmap(f.fileno(),0,access=mmap.ACCESS_COPY) as view:
    self.assertEqual(view[:],b'q'*8192);result=m.release_clean_mappings(p);self.assertGreaterEqual(result['mappings'],1);self.assertEqual(view[:],b'q'*8192)
if __name__=='__main__':unittest.main()
