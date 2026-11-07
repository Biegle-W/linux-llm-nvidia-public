import sys,io,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'network'),str(ROOT/'scripts')]
import worker_manager as m
class Wait(unittest.TestCase):
 def test_switch_waits_for_native_bolt_before_stopping(self):
  for profile in ['bolt-llamacpp']:
   with self.subTest(profile=profile),tempfile.TemporaryDirectory() as tmp:
    w=m.Workers.__new__(m.Workers);w.active=profile;w.key='fixture';w.wait_native_idle=lambda progress:None;w.detect=lambda:None;progress=[];stopped=[]
    class Done(Exception):pass
    def stop(**kw):stopped.append(True);raise Done()
    w.stop_owned=stop
    responses=[io.BytesIO(b'llamacpp:requests_processing 1\nllamacpp:requests_deferred 0\n'),io.BytesIO(b'llamacpp:requests_processing 0\nllamacpp:requests_deferred 0\n')]
    with patch.object(m,'ROOT',Path(tmp)),patch.object(m.OPENER,'open',side_effect=responses) as api,patch.object(m.time,'sleep') as sleep,self.assertRaises(Done):w.start('next',lambda:progress.append(True))
    self.assertEqual(len(progress),1);self.assertEqual(len(stopped),1);self.assertEqual(api.call_count,2);sleep.assert_called_once_with(1)
if __name__=='__main__':unittest.main()
