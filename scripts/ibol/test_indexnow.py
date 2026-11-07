import copy
import unittest
from urllib.error import HTTPError
from scripts.ibol.notify_indexnow import notify, validate


KEY = 'a' * 32
PAYLOAD = {'host': 'albertito-ai.github.io', 'key': KEY,
           'keyLocation': 'https://albertito-ai.github.io/Albertito-AI/' + KEY + '.txt',
           'urlList': ['https://albertito-ai.github.io/Albertito-AI/ibol/']}


class Response:
    def __init__(self, status, data, url): self.status, self.data, self.url = status, data, url
    def __enter__(self): return self
    def __exit__(self, *args): return False
    def read(self, limit): return self.data[:limit]
    def geturl(self): return self.url


class IndexNowTests(unittest.TestCase):
    def test_dry_run_has_no_network(self):
        def forbidden(*args, **kwargs): raise AssertionError('Unexpected network')
        self.assertEqual(notify(PAYLOAD, opener=forbidden)['state'], 'dry_run')

    def test_unowned_or_unreviewed_urls_rejected(self):
        for url in ['https://books.ugp.rug.nl/ugp/catalog/book/300',
                    'https://albertito-ai.github.io/other/',
                    'https://albertito-ai.github.io/Albertito-AI/ibol/embed.html',
                    'https://albertito-ai.github.io/Albertito-AI/ibol/?tracking=x']:
            p = copy.deepcopy(PAYLOAD); p['urlList'] = [url]
            with self.assertRaises(ValueError): validate(p)

    def test_wrong_proof_prevents_submission(self):
        calls = []
        def opener(req, **kwargs):
            calls.append(req.get_method())
            return Response(200, b'wrong', req.full_url)
        result = notify(PAYLOAD, True, opener)
        self.assertEqual(result['state'], 'proof_unverified')
        self.assertEqual(calls, ['GET'])
        self.assertFalse(result['submitted'])

    def test_receipts_do_not_infer_indexing_and_never_retry(self):
        for status, state in [(200, 'received'), (202, 'received_key_validation_pending'), (429, 'not_accepted')]:
            calls = []
            def opener(req, **kwargs):
                calls.append(req.get_method())
                return Response(200, KEY.encode(), req.full_url) if len(calls) == 1 else Response(status, b'', req.full_url)
            result = notify(PAYLOAD, True, opener)
            self.assertEqual(result['state'], state)
            self.assertEqual(calls, ['GET', 'POST'])
            self.assertEqual(result['received'], status in (200, 202))
            self.assertIn('No evidence', result['meaning'])

    def test_redirected_notification_is_not_a_receipt(self):
        calls = []
        def opener(req, **kwargs):
            calls.append(req.get_method())
            return Response(200, KEY.encode(), req.full_url) if len(calls) == 1 else Response(200, b'HTML', 'https://example.com/')
        result = notify(PAYLOAD, True, opener)
        self.assertEqual(result['state'], 'delivery_unknown')
        self.assertFalse(result['received'])


if __name__ == '__main__': unittest.main()
