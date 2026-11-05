"""Keep public binary export restricted to reviewed, metadata-free sample bytes."""
import hashlib
import importlib.util
import json
from pathlib import Path
import struct
import unittest
import zlib

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('sample_export',ROOT/'scripts/sync_public.py')
export=importlib.util.module_from_spec(spec);spec.loader.exec_module(export)

class PublicSampleTests(unittest.TestCase):
    def records(self):
        rows=json.loads((ROOT/'assets/samples/comfy/manifest.json').read_text())['samples'];records={}
        for row in rows:
            base='assets/samples/comfy/'
            records[base+row['file']]={'sha256':row['sha256'],'bytes':row['bytes']}
            if row.get('poster'):records[base+row['poster']]={'sha256':row['poster_sha256'],'bytes':row['poster_bytes']}
        return records
    def test_only_reviewed_samples_match_receipts(self):
        records=self.records();self.assertEqual(set(records),set(export.SAMPLE_MEDIA))
        for name in records:
            self.assertIn(name,export.FILES)
            self.assertNotIn(name,export.RETIRED_FILES)
            export.validate_sample_media(name,(ROOT/name).read_bytes(),records)
    def test_changed_sample_rejected(self):
        name=export.SAMPLE_MEDIA[0]
        with self.assertRaisesRegex(AssertionError,'content changed'):
            export.validate_sample_media(name,(ROOT/name).read_bytes()+b'changed',self.records())
    def test_png_metadata_rejected_even_with_updated_receipt(self):
        name=export.SAMPLE_MEDIA[0];original=(ROOT/name).read_bytes();text=b'prompt\x00private workflow'
        chunk=struct.pack('>I',len(text))+b'tEXt'+text+struct.pack('>I',zlib.crc32(b'tEXt'+text))
        content=original[:-12]+chunk+original[-12:]
        records={name:{'sha256':hashlib.sha256(content).hexdigest(),'bytes':len(content)}}
        with self.assertRaisesRegex(AssertionError,'metadata chunk'):export.validate_sample_media(name,content,records)
    def test_arbitrary_binary_path_rejected(self):
        with self.assertRaisesRegex(AssertionError,'Unreviewed binary'):
            export.validate_sample_media('data/private.png',b'',{})
