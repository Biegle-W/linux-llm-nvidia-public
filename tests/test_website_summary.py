"""docs/WEBSITE-SUMMARY.md feeds the owner's website; it must match the router catalog."""
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from profile_catalog import load_catalog

SUMMARY = ROOT / 'docs/WEBSITE-SUMMARY.md'
SECTIONS = ('## Enabled routes', '## Speed (standard short tool-call check)', '## Retired or removed routes',
            '## Quality ranking (390-item test)', '## Short tool-use test', '## Trials (not router entries)',
            '## Hardware and measurement conditions')


def section(text, heading):
    start = text.index(heading)
    nxt = text.find('\n## ', start + len(heading))
    return text[start:nxt if nxt >= 0 else len(text)]


def first_column_ids(block):
    return {m.group(1) for m in re.finditer(r'^\|\s*`?([a-z0-9][a-z0-9.-]+)`?\s*\|', block, re.M)}


class WebsiteSummary(unittest.TestCase):
    def setUp(self):
        self.text = SUMMARY.read_text()
        self.enabled = {p['id'] for p in load_catalog()['profiles']}

    def test_sections_in_order(self):
        positions = [self.text.index(h) for h in SECTIONS]
        self.assertEqual(positions, sorted(positions))

    def test_enabled_routes_and_speed_rows_match_the_catalog(self):
        for heading in SECTIONS[:2]:
            with self.subTest(section=heading):
                self.assertEqual(first_column_ids(section(self.text, heading)) & (self.enabled | self.retired()), self.enabled)

    def test_retired_routes_are_not_listed_as_enabled(self):
        listed = first_column_ids(section(self.text, SECTIONS[2]))
        self.assertTrue(listed, 'retired table is empty')
        self.assertFalse(listed & self.enabled)

    def retired(self):
        return first_column_ids(section(self.text, SECTIONS[2]))

    def test_trials_are_marked_not_for_the_website(self):
        block = section(self.text, SECTIONS[5])
        rows = [l for l in block.splitlines() if l.startswith('|') and not set(l) <= set('|-: ')][1:]
        for row in rows:
            with self.subTest(row=row[:60]):
                self.assertIn('trial, not for the website', row)
