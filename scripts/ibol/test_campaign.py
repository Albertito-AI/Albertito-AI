"""Check that campaign counts and linked deliverables match actual recorded work."""
import json
import re
import subprocess
from pathlib import Path
import unittest
from urllib.parse import urlsplit

SITE = Path(__file__).resolve().parents[2] / 'site/ibol'


class CampaignEvidenceTests(unittest.TestCase):
    def test_assignment_identity_and_counts(self):
        data = json.loads((SITE / 'data/campaign-66.json').read_text())
        expected = {f'R{n:02d}-{lane}' for n in range(1, 12) for lane in 'ABCDEF'}
        items = data['assignments']
        self.assertEqual(len(items), 66)
        self.assertEqual({x['task_id'] for x in items}, expected)
        self.assertEqual(data['worker_count'], 6)
        complete = [x for x in items if x['status'] == 'completed']
        self.assertEqual(data['completed_assignments'], len(complete))
        self.assertLessEqual(len({x['agent'] for x in complete}), 6)
        for x in complete:
            self.assertTrue(x['outcome'])
            self.assertTrue(x.get('checks') or x.get('evidence'))
            self.assertEqual(x['task_id'], f"R{x['round']:02d}-{x['lane']}")

    def test_study_lab_boundaries_and_recall_behaviour(self):
        result = subprocess.run(['node', str(SITE.parents[1] / 'scripts/ibol/check_study_lab.cjs')], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_portable_cards_preserve_sources_and_rights(self):
        export = json.loads((SITE / 'activities/study-cards.json').read_text())
        page = (SITE / 'activities/study-lab.html').read_text()
        embedded = re.search(r'<script id="study-card-data" type="application/json">(.*?)</script>', page, re.S)
        self.assertIsNotNone(embedded)
        self.assertEqual(export['cards'], json.loads(embedded.group(1)))
        self.assertEqual(len(export['cards']), 8)
        self.assertEqual(len({card['id'] for card in export['cards']}), 8)
        self.assertEqual(export['licence']['identifier'], 'CC-BY-4.0')
        self.assertEqual(export['source_book']['licence'], 'CC BY-NC-ND 4.0')
        for card in export['cards']:
            self.assertEqual(card['source_url'].split('#page=')[1], str(card['pages'][0] + 2))

    def test_public_evidence_and_files(self):
        data = json.loads((SITE / 'data/campaign-66.json').read_text())
        for item in data['assignments']:
            for evidence in item.get('evidence', []):
                url = urlsplit(evidence['url'])
                self.assertEqual(url.scheme, 'https')
                self.assertTrue(url.netloc)
                self.assertIsNone(url.username)
                self.assertIsNone(url.password)
                self.assertTrue(evidence['observation'])
            for filename in item.get('files', []):
                self.assertNotIn('..', Path(filename).parts)
                self.assertTrue((SITE.parents[1] / filename).is_file(), filename)
        raw = json.dumps(data)
        self.assertNotIn('/workspace/', raw)
        self.assertNotIn('siwc_bypass_bearer_token', raw)


if __name__ == '__main__':
    unittest.main()
