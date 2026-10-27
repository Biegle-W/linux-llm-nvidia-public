"""Sensor absence and bounded logging are independent of inference correctness."""
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from lifecycle_telemetry import LifecycleLog,numeric


class LifecycleTest(unittest.TestCase):
    def test_unavailable_sensor_is_not_zero(self):
        self.assertIsNone(numeric('[N/A]'));self.assertEqual(numeric(' 52.0 '),52)
        self.assertEqual(numeric('P2'),'P2')
    def test_start_stop_and_rotation_preserve_bounded_private_logs(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'lifecycle.jsonl';log=LifecycleLog('fixture',path=path,limit_bytes=500)
            with patch('lifecycle_telemetry.gpu_sample',return_value=[{'index':0,'temperature.gpu':52}]),patch('lifecycle_telemetry.cpu_and_board_sample',return_value={'cpu_mhz_max':4900}):
                log.start();log.set_phase('inference');log.stop(0)
                log.event('extra',value='x'*600);log.event('rotated')
            files=list(Path(directory).glob('*.jsonl'))
            self.assertLessEqual(len(files),3)
            rows=[json.loads(line) for p in files for line in p.read_text().splitlines()]
            self.assertIn('stopped',[r['event'] for r in rows])
            self.assertFalse(path.stat().st_mode&0o077)


if __name__=='__main__':unittest.main()
