import copy
import io
import json
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from stage_engine_candidate import digest, evaluate, extract_snapshot, stage


class CandidateStaging(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / 'config').mkdir()
        (self.root / 'config/maintained-profiles.json').write_text(json.dumps(
            {'profiles': [{'id': 'kept', 'allocated_context': 8192}]}))
        self.source = self.root / 'upstream'
        self.source.mkdir()
        subprocess.run(['git', 'init', '-q', str(self.source)], check=True)
        (self.source / 'source.txt').write_text('pinned source\n')
        subprocess.run(['git', '-C', str(self.source), 'add', 'source.txt'], check=True)
        subprocess.run(['git', '-C', str(self.source), '-c', 'user.name=Candidate Test',
                        '-c', 'user.email=test@example.invalid', 'commit', '-qm', 'fixture'], check=True)
        self.commit = subprocess.check_output(['git', '-C', str(self.source), 'rev-parse', 'HEAD'], text=True).strip()
        self.fixture = self.root / 'prose.json'
        self.fixture.write_text('{"messages":[]}\n')

    def prepare(self):
        return stage(self.source, self.commit, 'kept', 'candidate-one', [self.fixture], self.root)

    def test_exact_commit_snapshot_does_not_copy_working_changes_or_activate(self):
        (self.source / 'source.txt').write_text('uncommitted change')
        target = self.prepare()
        self.assertEqual((target / 'source/source.txt').read_text(), 'pinned source\n')
        self.assertFalse((target / 'source/.git').exists())
        self.assertEqual(json.loads((target / 'manifest.json').read_text())['status'], 'staged-unbuilt')
        with self.assertRaises(FileExistsError):
            self.prepare()
        with self.assertRaises(ValueError):
            stage(self.source, 'main', 'kept', 'another', [self.fixture], self.root)

    def test_escaping_source_links_are_refused(self):
        data = io.BytesIO()
        with tarfile.open(fileobj=data, mode='w') as tar:
            info = tarfile.TarInfo('outside')
            info.type, info.linkname = tarfile.SYMTYPE, '../../other'
            tar.addfile(info)
        with self.assertRaises(ValueError):
            extract_snapshot(data.getvalue(), self.root / 'safe')

    def records(self):
        raw = self.root / 'raw.json'
        raw.write_text('{"requests":3}')
        record = dict(profile_id='kept', source_commit=self.commit,
                      model_quant_fingerprint='same-weights', settings_sha256='settings',
                      hardware_fingerprint='same-cards-and-boot',
                      fixture_sha256={'prose': digest(self.fixture)},
                      context=8192, repetitions=3, input_tokens=[2200, 2201, 2202],
                      output_tokens=128, prefill_tps=100, ttft_s=22, decode_tps=10,
                      quality=dict(json=True, arithmetic=True, near_window_retrieval=True,
                                   retrieval_input_tokens=7300),
                      resources=dict(owned_worker=True, ram_limits=True, host_floor=True,
                                     gpu_headroom=True, thermal=True, active_swap_guard=True,
                                     guard_stops=0), raw_evidence={'raw.json': digest(raw)})
        baseline, candidate = self.root / 'baseline.json', self.root / 'candidate.json'
        baseline.write_text(json.dumps(record))
        candidate.write_text(json.dumps(record))
        return baseline, candidate, copy.deepcopy(record)

    def test_review_accepts_matched_evidence_without_activation(self):
        target = self.prepare()
        b, c, _ = self.records()
        result = evaluate(target, b, c)
        self.assertTrue(result['accepted_for_manual_review'])
        self.assertEqual(json.loads((target / 'manifest.json').read_text())['status'], 'staged-unbuilt')

    def test_speed_quality_context_and_resource_failures_are_rejected(self):
        target = self.prepare()
        b, c, record = self.records()
        record['decode_tps'] = 9
        record['context'] = 4096
        record['resources']['active_swap_guard'] = False
        record['quality']['arithmetic'] = False
        c.write_text(json.dumps(record))
        result = evaluate(target, b, c)
        self.assertFalse(result['accepted_for_manual_review'])
        self.assertGreaterEqual(len(result['reasons']), 4)

    def test_changed_raw_evidence_fails_closed(self):
        target = self.prepare()
        b, c, _ = self.records()
        (self.root / 'raw.json').write_text('changed')
        with self.assertRaises(ValueError):
            evaluate(target, b, c)


if __name__ == '__main__':
    unittest.main()
