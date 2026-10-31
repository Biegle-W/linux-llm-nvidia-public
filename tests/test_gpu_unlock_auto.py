import unittest,tempfile,subprocess,os,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import gpu_unlock_health as health
ROOT=Path(__file__).resolve().parents[1]
HOOK=ROOT/'scripts/dracut/91local-llm-gpu-unlock/unlock-auto.sh'
class AutoUnlock(unittest.TestCase):
 def setup_tree(self,base,shift=0):
  for bdf,model in [(f'0000:{10+shift:02x}:00.0','0x2208'),(f'0000:{18+shift:02x}:00.0','0x2206'),('0000:1c:00.0','0x2503')]:
   p=base/bdf;p.mkdir(parents=True)
   for n,v in [('vendor','0x10de'),('class','0x030000'),('device',model)]: (p/n).write_text(v+'\n')
 def config(self):return {'selection_mode':'boot-model-ids','approved_device_ids':['0x2206','0x2208','0x2503'],'targets':[]}
 def test_resolves_changed_bus_addresses(self):
  for shift in [0,2,7]:
   with tempfile.TemporaryDirectory() as d:
    base=Path(d);self.setup_tree(base,shift)
    got=health.resolve_config(self.config(),base)
    self.assertEqual({x['device'] for x in got['targets']},{'0x2206','0x2208','0x2503'})
    self.assertIn(f'0000:{10+shift:02x}:00.0',{x['bdf'] for x in got['targets']})
 def test_refuses_missing_or_duplicate_model(self):
  for model in ['0x2206','0xffff']:
   with tempfile.TemporaryDirectory() as d:
    base=Path(d);self.setup_tree(base);(base/'0000:1c:00.0/device').write_text(model)
    with self.assertRaises(ValueError):health.resolve_config(self.config(),base)
 def test_auto_fingerprint_ignores_bus_renumbering(self):
  from unittest.mock import patch
  c=self.config();c.update(grub_dropin='/tmp/nonexistent-grub',dracut_dropin='/tmp/nonexistent-dracut',auto_hook='/tmp/no-hook',auto_module_setup='/tmp/no-setup')
  with tempfile.TemporaryDirectory() as a,tempfile.TemporaryDirectory() as b:
   self.setup_tree(Path(a),0);self.setup_tree(Path(b),4)
   with patch.object(health,'run',return_value='/tmp/no-module'):
    self.assertEqual(health.fingerprint(health.resolve_config(c,Path(a)),'test',[]),health.fingerprint(health.resolve_config(c,Path(b)),'test',[]))
 def test_hook_passes_current_addresses_before_driver(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);base=p/'pci';base.mkdir();self.setup_tree(base,3)
   (p/'cmdline').write_text('quiet local_llm_gpu_unlock=auto iommu=pt\n')
   run=p/'run';bin=p/'bin';bin.mkdir();capture=p/'capture'
   m=bin/'modprobe';m.write_text('#!/bin/sh\nprintf "%s\\n" "$@" > "$TEST_CAPTURE"\n');m.chmod(0o755)
   text=HOOK.read_text().replace('/sys/bus/pci/devices',str(base)).replace('/proc/cmdline',str(p/'cmdline')).replace('/run/',str(run)+'/')
   hook=p/'hook.sh';hook.write_text(text)
   subprocess.run(['/bin/sh',str(hook)],env=dict(os.environ,PATH=str(bin)+':'+os.environ['PATH'],TEST_CAPTURE=str(capture)),check=True,capture_output=True)
   self.assertEqual(capture.read_text().splitlines()[0],'gpu_unlock')
   args=capture.read_text();self.assertIn('0000:0d:00.0',args);self.assertIn('0000:15:00.0',args);self.assertIn('0000:1c:00.0',args)
   opts=(run/'modprobe.d/local-llm-dynamic-bar1.conf').read_text();self.assertIn('RMForceStaticBar1=0',opts);self.assertNotIn('pci=0000:1c:00.0',opts)
if __name__=='__main__':unittest.main()
