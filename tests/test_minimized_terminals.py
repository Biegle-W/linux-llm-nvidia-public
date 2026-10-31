"""Only backend monitors minimize; attention terminals map in the foreground."""
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


if __name__=='__main__':unittest.main()
