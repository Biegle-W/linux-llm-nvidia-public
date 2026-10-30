"""Search validation/parser and HTTP integration with a mock provider/worker."""
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'network'))
import web_search as ws
from worker_manager import RouterError
import test_router

ROWS = [{'url': 'https://science.nasa.gov/mars/facts/', 'title': 'Mars facts',
         'snippet': 'Iron oxidizes and gives Mars its red appearance.'}]


class SearchTests(unittest.TestCase):
    def body(self, **kw):
        return dict({'model': 'qwen27b-hyperqwen', 'input': 'NASA Mars red',
                     'tools': [{'type': 'web_search'}]}, **kw)

    def test_options_and_latest_user_only(self):
        data = self.body(input=[{'role': 'system', 'content': 'private instructions'},
                                {'role': 'user', 'content': 'old private query'},
                                {'role': 'assistant', 'content': 'old answer'},
                                {'role': 'user', 'content': [{'type': 'input_text', 'text': 'NASA Mars red'},
                                                             {'type': 'input_image', 'image_url': 'secret'}]}])
        self.assertEqual(ws.plan(data)['query'], 'NASA Mars red')
        data['input'] = 'x' * 10000
        self.assertEqual(len(ws.plan(data)['query']), 512)

    def test_versions_and_disabling(self):
        for kind in ws.SEARCH_TYPES:
            self.assertEqual(ws.plan(self.body(tools=[{'type': kind}]))['limit'], 5)
        self.assertTrue(ws.plan(self.body(tool_choice='none'))['disabled'])
        self.assertTrue(ws.plan(self.body(tool_choice={'type': 'function', 'name': 'other'}))['disabled'])
        self.assertIsNone(ws.plan({'input': 'hi'}))

    def test_unsupported_modes_fail_explicitly(self):
        for tool in [{'type': 'web_search', 'external_web_access': False},
                     {'type': 'web_search', 'filters': {'blocked_domains': ['bad.com']}},
                     {'type': 'web_search', 'filters': {'allowed_domains': ['https://nasa.gov']}},
                     {'type': 'web_search', 'user_location': {'country': 'CA'}},
                     {'type': 'web_search', 'search_context_size': 'huge'}]:
            with self.assertRaises(RouterError):
                ws.plan(self.body(tools=[tool]))
        for kw in [{'previous_response_id': 'resp_old'}, {'input': []}, {'include': None},
                   {'instructions': []}, {'tools': {}}, {'tool_choice': []}]:
            with self.assertRaises(RouterError):
                ws.plan(self.body(**kw))

    def test_parser_unwraps_links_and_rejects_local_urls(self):
        p = ws.ResultsParser()
        p.feed('<a class="result-link" href="//duckduckgo.com/l/?uddg=https%3A%2F%2Fnasa.gov%2F">NASA &amp; Mars</a>'
               '<td class="result-snippet">Iron <b>oxide</b> red</td>'
               '<a class="result-link" href="http://127.0.0.1/admin">local</a>')
        self.assertEqual(p.rows, [{'url': 'https://nasa.gov/', 'title': 'NASA & Mars', 'snippet': 'Iron oxide red'}])
        for url in ['file:///etc/passwd', 'http://localhost/', 'http://192.168.1.1', 'http://x.local', 'https://user:pass@example.com']:
            self.assertFalse(ws.public_url(url))

    def test_annotations_only_reference_real_search_results(self):
        text = 'Iron [1], invented [99].'
        values = ws.annotations(text, ROWS)
        self.assertEqual(len(values), 1)
        self.assertEqual(text[values[0]['start_index']:values[0]['end_index']], '[1]')
        self.assertEqual(values[0]['url'], ROWS[0]['url'])

    def test_challenge_fallback_filters_and_bounded_fetch(self):
        from io import BytesIO
        class Response(BytesIO):
            status = 200
        challenge = Response(b'challenge')
        challenge.status = 202
        good = Response(b'<a class="result__a" href="https://evilnasa.gov/">Excluded</a>'
                        b'<a class="result__a" href="https://science.nasa.gov/mars/">Mars</a>'
                        b'<a class="result__snippet">Iron <b>oxide</b></a>')
        opener = SimpleNamespace(open=unittest.mock.Mock(side_effect=[challenge, good]))
        with patch.object(ws.urllib.request, 'build_opener', return_value=opener), patch.object(ws, 'SEARCH_CONFIG') as cfg:
            cfg.exists.return_value = True
            cfg.read_text.return_value = '{"provider":"duckduckgo"}'
            rows = ws.search('Mars', ['nasa.gov'])
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]['snippet'], 'Iron oxide')
        self.assertEqual(opener.open.call_count, 2)
        for call in opener.open.call_args_list:
            self.assertEqual(call.kwargs['timeout'], 12)
            self.assertEqual(set(call.args[0].headers), {'User-agent', 'Accept'})

    def test_provider_failure_is_bounded_and_explicit(self):
        opener = SimpleNamespace(open=unittest.mock.Mock(side_effect=OSError('network down')))
        with patch.object(ws.urllib.request, 'build_opener', return_value=opener), patch.object(ws, 'SEARCH_CONFIG') as cfg:
            cfg.exists.return_value = True
            cfg.read_text.return_value = '{"provider":"duckduckgo"}'
            with self.assertRaisesRegex(RouterError, 'no usable results'):
                ws.search('Mars')
        self.assertEqual(opener.open.call_count, 2)

    def test_brave_key_is_private_and_never_returned_on_provider_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            key = Path(tmp) / 'key'
            key.write_text('test-search-secret')
            key.chmod(0o644)
            with self.assertRaisesRegex(RouterError, 'private owner-only'):
                ws.brave_search('Mars', [], 3, {'key_file': str(key)})
            key.chmod(0o600)
            opener = SimpleNamespace(open=unittest.mock.Mock(side_effect=OSError('test-search-secret')))
            with patch.object(ws.urllib.request, 'build_opener', return_value=opener):
                with self.assertRaises(RouterError) as error:
                    ws.brave_search('Mars', [], 3, {'key_file': str(key)})
            self.assertNotIn('test-search-secret', str(error.exception))
            req = opener.open.call_args.args[0]
            self.assertEqual(req.get_header('X-subscription-token'), 'test-search-secret')
            self.assertEqual(ws.urlsplit(req.full_url).hostname, 'api.search.brave.com')

    def test_keyless_default_dispatches_to_mwmbl(self):
        with patch.object(ws, 'SEARCH_CONFIG') as cfg, patch.object(ws, 'mwmbl_search', return_value=ROWS) as provider:
            cfg.exists.return_value = False
            self.assertEqual(ws.search('Mars', ['nasa.gov'], 3), ROWS)
        provider.assert_called_once_with('Mars', ['nasa.gov'], 3)

    def test_mwmbl_anonymous_headers_filtering_and_rate_limit(self):
        from io import BytesIO
        class Response(BytesIO):
            status = 200
        raw = {'results': [{'url': ROWS[0]['url'], 'title': 'Mars', 'content': 'Iron\noxide'},
                           {'url': 'https://evilnasa.gov/', 'title': 'Excluded'},
                           {'url': ROWS[0]['url'], 'title': 'Duplicate'}]}
        opener = SimpleNamespace(open=unittest.mock.Mock(return_value=Response(json.dumps(raw).encode())))
        with patch.object(ws.urllib.request, 'build_opener', return_value=opener), \
             patch.object(ws, '_mwmbl_last_request', 100), patch.object(ws.time, 'monotonic', return_value=100.2), \
             patch.object(ws.time, 'sleep') as sleep:
            result = ws.mwmbl_search('Mars', ['nasa.gov'], 5)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['snippet'], 'Iron oxide')
        self.assertAlmostEqual(sleep.call_args.args[0], .85)
        req = opener.open.call_args.args[0]
        self.assertEqual(set(req.headers), {'User-agent', 'Accept'})
        self.assertEqual(ws.urlsplit(req.full_url).hostname, 'api.mwmbl.org')
        self.assertEqual(ws.parse_qs(ws.urlsplit(req.full_url).query), {'q': ['Mars']})

    def test_mwmbl_quota_error_is_explicit_without_retries(self):
        opener = SimpleNamespace(open=unittest.mock.Mock(side_effect=OSError('quota reached')))
        with patch.object(ws.urllib.request, 'build_opener', return_value=opener), patch.object(ws, '_mwmbl_last_request', 0):
            with self.assertRaisesRegex(RouterError, 'anonymous quota'):
                ws.mwmbl_search('Mars', [], 5)
        self.assertEqual(opener.open.call_count, 1)

    def test_brave_parses_filters_and_deduplicates(self):
        from io import BytesIO
        class Response(BytesIO):
            status = 200
        with tempfile.TemporaryDirectory() as tmp:
            key = Path(tmp) / 'key'
            key.write_text('test-search-secret')
            key.chmod(0o600)
            rows = [{'url': ROWS[0]['url'], 'title': 'Mars', 'description': 'Iron oxide'},
                    {'url': 'https://evilnasa.gov/', 'title': 'No'},
                    {'url': ROWS[0]['url'], 'title': 'Duplicate'}]
            opener = SimpleNamespace(open=unittest.mock.Mock(return_value=Response(json.dumps({'web': {'results': rows}}).encode())))
            with patch.object(ws.urllib.request, 'build_opener', return_value=opener):
                result = ws.brave_search('Mars', ['nasa.gov'], 5, {'key_file': str(key)})
            self.assertEqual(len(result), 1)
            self.assertEqual(result[0]['snippet'], 'Iron oxide')

    def test_tools_preserve_functions_and_original_request(self):
        function = {'type': 'function', 'name': 'weather'}
        data = self.body(tools=[{'type': 'web_search'}, function], tool_choice={'type': 'web_search'})
        result = ws.strip_tools(data)
        self.assertEqual(result['tools'], [function])
        self.assertEqual(result['tool_choice'], 'auto')
        self.assertEqual(len(data['tools']), 2)


class SearchHTTPTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        test_router.RouterTest.setUpClass()

    @classmethod
    def tearDownClass(cls):
        test_router.RouterTest.tearDownClass()

    def request(self, body, key=test_router.KEY):
        fixture = test_router.RouterTest()
        return fixture.request('/v1/responses', body, key=key)

    def body(self, **kw):
        return dict({'model': 'qwen27b-hyperqwen', 'input': 'NASA Mars red',
                     'tools': [{'type': 'web_search_preview'}], 'include': ['web_search_call.action.sources']}, **kw)

    def test_nonstream_search_grounding_sources_and_citations(self):
        with patch.object(ws, 'search', return_value=ROWS) as search:
            status, raw = self.request(self.body(instructions='Be concise.'))
        self.assertEqual(status, 200)
        value = json.loads(raw)
        self.assertEqual(value['model'], 'qwen27b-hyperqwen')
        self.assertEqual(value['output'][0]['type'], 'web_search_call')
        self.assertEqual(value['output'][0]['action']['sources'][0]['url'], ROWS[0]['url'])
        self.assertEqual(value['output'][1]['content'][0]['annotations'][0]['url'], ROWS[0]['url'])
        body = test_router.RouterTest.backend.body
        self.assertNotIn('tools', body)
        self.assertTrue(body['instructions'].startswith('Be concise.'))
        self.assertIn('UNTRUSTED', body['instructions'])
        self.assertIn(ROWS[0]['snippet'], body['instructions'])
        self.assertEqual(body['input'], 'NASA Mars red')
        search.assert_called_once_with('NASA Mars red', [], 5)
        self.assertFalse(test_router.RouterTest.server.workers.busy)

    def test_stream_lifecycle_output_indices_and_citations(self):
        with patch.object(ws, 'search', return_value=ROWS):
            status, raw = self.request(self.body(stream=True))
        self.assertEqual(status, 200)
        events = [json.loads(line[5:]) for line in raw.splitlines() if line.startswith(b'data:')]
        types = [v['type'] for v in events]
        self.assertEqual(types[0], 'response.created')
        self.assertEqual(types[-1], 'response.completed')
        self.assertIn('response.web_search_call.searching', types)
        self.assertIn('response.output_text.annotation.added', types)
        self.assertEqual([v['sequence_number'] for v in events], list(range(len(events))))
        self.assertEqual(events[0]['response']['id'], events[-1]['response']['id'])
        delta = next(v for v in events if v['type'] == 'response.output_text.delta')
        self.assertEqual(delta['output_index'], 1)
        completed = events[-1]['response']
        self.assertEqual([v['type'] for v in completed['output']], ['web_search_call', 'message'])
        self.assertEqual(completed['output'][1]['content'][0]['annotations'][0]['url'], ROWS[0]['url'])

    def test_none_and_function_choice_never_search(self):
        with patch.object(ws, 'search') as search:
            status, raw = self.request(self.body(tool_choice='none'))
        self.assertEqual(status, 200)
        search.assert_not_called()
        self.assertEqual(json.loads(raw)['output'][0]['type'], 'message')
        self.assertNotIn('tools', test_router.RouterTest.backend.body)

    def test_failure_is_explicit_and_slot_released(self):
        for stream in (False, True):
            with patch.object(ws, 'search', side_effect=RouterError('Provider unavailable', 'web_search_unavailable', 503)):
                status, raw = self.request(self.body(stream=stream))
            self.assertEqual(status, 200 if stream else 503)
            self.assertIn(b'web_search_unavailable', raw)
            self.assertNotIn(b'response.completed', raw)
            self.assertFalse(test_router.RouterTest.server.workers.busy)
            if stream:
                events = [json.loads(line[5:]) for line in raw.splitlines() if line.startswith(b'data:')]
                self.assertEqual(events[-1]['type'], 'error')
                self.assertEqual([v['sequence_number'] for v in events], list(range(len(events))))

    def test_auth_and_validation_precede_search_and_worker(self):
        with patch.object(ws, 'search') as search, patch.object(test_router.RouterTest.server.workers, 'acquire') as acquire:
            self.assertEqual(self.request(self.body(), key='bad')[0], 401)
            self.assertEqual(self.request(self.body(tools=[{'type': 'web_search', 'external_web_access': False}]))[0], 400)
        search.assert_not_called()
        acquire.assert_not_called()


if __name__ == '__main__':
    unittest.main()
