"""Automated jobs minimize; selectors and explicit attention tasks can focus."""
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'network')]
import visible_terminal as terminal
import install as installer


class MinimizedTerminals(unittest.TestCase):
    def test_only_backend_terminal_requests_native_iconic_state(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);(root/'config').mkdir();(root/'bin').mkdir();binary=root/'bin/xterm';binary.write_bytes(b'fixture-binary')
            (root/'config/terminal-runtime.json').write_text(json.dumps({'binary':'bin/xterm','sha256':{'bin/xterm':hashlib.sha256(binary.read_bytes()).hexdigest()}}))
            with patch.object(terminal,'ROOT',root):
                command=terminal.terminal_command('Fixture',['/usr/bin/python3','fixture.py'],minimized=True)
                attention=terminal.terminal_command('Password',['/bin/true'])
            self.assertIn('-iconic',command[:command.index('-e')]);self.assertNotIn('-iconic',attention);self.assertEqual(command[-2:],['/usr/bin/python3','fixture.py'])

    def test_tampered_runtime_cannot_fall_back_to_a_focus_stealing_terminal(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);(root/'config').mkdir();(root/'bin').mkdir();(root/'bin/xterm').write_bytes(b'changed')
            (root/'config/terminal-runtime.json').write_text(json.dumps({'binary':'bin/xterm','sha256':{'bin/xterm':'invalid'}}))
            with patch.object(terminal,'ROOT',root),patch.object(terminal,'launch_terminal') as launch:
                with self.assertRaises(RuntimeError):terminal.terminal_command('Fixture',['/bin/true'])
                launch.assert_not_called()

    def test_all_four_shortcuts_use_the_shared_selector_without_default_terminal(self):
        for engine,label in [('hyperqwen','HyperQwen vLLM'),('sglang','SGLang'),('strata','Strata'),('maya','Maya')]:
            text=installer.engine_desktop(engine,label,Path('fixture-icon.svg'))
            self.assertIn('Terminal=false',text);self.assertNotIn('Terminal=true',text)
            self.assertIn('visible_terminal.py" launch',text);self.assertIn('--engine '+engine,text)



class LaunchPresentation(unittest.TestCase):
    def launch(self,mode,extra):
        with tempfile.TemporaryDirectory() as directory:
            state=Path(directory)
            def start(command):
                receipt=next(state.glob('harness-*.json'),None)
                # main allocates a name but does not create its receipt before launch.
                receipt=Path(command[command.index('--receipt')+1])
                receipt.write_text(json.dumps({'state':'running','window_id':'42'}))
            def command(title,child,minimized=False):return child
            with patch.object(terminal,'STATE',state),patch.object(sys,'argv',['visible_terminal.py',mode,*extra,'--','/bin/true']),patch.object(terminal,'launch_terminal',side_effect=start),patch.object(terminal,'terminal_command',side_effect=command) as build,patch.object(terminal,'focus_terminal') as focus:
                terminal.main();return build.call_args.kwargs['minimized'],focus.call_count,build.call_args.args[1]
    def test_automated_run_never_focuses(self):
        minimized,focused,child=self.launch('run',[]);self.assertTrue(minimized);self.assertEqual(focused,0);self.assertIn('--minimized',child)
    def test_explicit_auth_attention_can_focus(self):
        minimized,focused,_=self.launch('run',['--attention']);self.assertFalse(minimized);self.assertEqual(focused,1)
    def test_user_selector_can_focus(self):
        minimized,focused,_=self.launch('launch',[]);self.assertFalse(minimized);self.assertEqual(focused,1)
    def test_explicit_quiet_selector_never_focuses(self):
        minimized,focused,_=self.launch('launch',['--minimized']);self.assertTrue(minimized);self.assertEqual(focused,0)

if __name__=='__main__':unittest.main()
