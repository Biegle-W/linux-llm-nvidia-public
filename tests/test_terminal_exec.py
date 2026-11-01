import hashlib,importlib.util,json,os,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
spec=importlib.util.spec_from_file_location('terminal_exec',ROOT/'scripts/terminal_exec.py');terminal=importlib.util.module_from_spec(spec);spec.loader.exec_module(terminal)
class Policy(unittest.TestCase):
 def test_background_detection_does_not_classify_attention_children(self):
  self.assertTrue(terminal.background(['-iconic','-e','/bin/true']))
  self.assertTrue(terminal.background(['-e','python3','/project/visible_terminal.py','watch','--unit','fixture.service']))
  self.assertFalse(terminal.background(['-e','python3','/project/visible_terminal.py','foreground','--attention']))
  self.assertFalse(terminal.background(['-e','python3','-c','-iconic']))
 def exercise(self,background):
  with tempfile.TemporaryDirectory() as directory:
   root=Path(directory);(root/'config').mkdir();(root/'native').write_bytes(b'fixture')
   (root/'config/terminal-runtime.json').write_text(json.dumps({'native_binary':'native','sha256':{'native':hashlib.sha256(b'fixture').hexdigest()}}))
   args=['terminal_exec.py',*(['-iconic'] if background else []),'-e','/bin/echo','literal; $(never executed)']
   with patch.object(terminal,'ROOT',root),patch.object(sys,'argv',args),patch.dict(os.environ,{'DESKTOP_STARTUP_ID':'fixture','XDG_ACTIVATION_TOKEN':'fixture'}),patch.object(terminal.os,'execve') as execute:terminal.main()
   return execute.call_args
 def test_legacy_background_gets_child_policy_and_no_tokens(self):
  call=self.exercise(True);argv=call.args[1];env=call.args[2]
  self.assertIn('--background-child',argv);self.assertIn('*allowWindowOps: false',argv);self.assertNotIn('DESKTOP_STARTUP_ID',env);self.assertNotIn('XDG_ACTIVATION_TOKEN',env);self.assertEqual(argv[-2:],['/bin/echo','literal; $(never executed)'])
 def test_explicit_attention_is_passed_through(self):
  call=self.exercise(False);self.assertNotIn('--background-child',call.args[1]);self.assertNotIn('-iconic',call.args[1]);self.assertEqual(call.args[2]['DESKTOP_STARTUP_ID'],'fixture')
 def test_child_protection_precedes_exact_exec(self):
  import visible_terminal
  with patch.object(sys,'argv',['terminal_exec.py','--background-child','--','/bin/echo','literal; $(not shell)']),patch.dict(os.environ,{'WINDOWID':'123'}),patch.object(visible_terminal,'background_terminal',return_value=True) as protect,patch.object(terminal.os,'execvpe') as execute:
   terminal.main();protect.assert_called_once_with('123');self.assertEqual(execute.call_args.args[:2],('/bin/echo',['/bin/echo','literal; $(not shell)']))
if __name__=='__main__':unittest.main()
