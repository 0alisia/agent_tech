import importlib.util
import os
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import patch


ENGINE_PATH = Path(__file__).resolve().parents[1] / 'chroma_engine.py'


class FakeAuthenticationError(Exception):
    pass


class FakeEmbeddings:
    def create(self, **kwargs):
        self.last_request = kwargs
        return types.SimpleNamespace(data=[
            types.SimpleNamespace(index=1, embedding=[2.0]),
            types.SimpleNamespace(index=0, embedding=[1.0]),
        ])


class FakeResponses:
    def create(self, **kwargs):
        if getattr(self, 'error', None):
            raise self.error
        self.last_request = kwargs
        if kwargs.get('stream'):
            return iter([
                types.SimpleNamespace(type='response.output_text.delta', delta='你好'),
                types.SimpleNamespace(type='response.output_text.delta', delta='，世界'),
            ])
        return types.SimpleNamespace(output_text='你好，世界')


class FakeOpenAI:
    def __init__(self, api_key, base_url=None):
        self.api_key = api_key
        self.base_url = base_url
        self.embeddings = FakeEmbeddings()
        self.responses = FakeResponses()


class OpenAIEngineTests(unittest.TestCase):
    def setUp(self):
        settings = types.SimpleNamespace(
            CHROMA_PERSIST_DIR='unused',
            OPENAI_API_KEY='test-openai-key',
            OPENAI_BASE_URL='',
            OPENAI_MODEL='gpt-6-sol',
            OPENAI_REASONING_EFFORT='high',
            OPENAI_EMBEDDING_MODEL='text-embedding-3-small',
            OPENAI_EMBEDDING_DIM=1024,
        )
        self.settings = settings
        fake_django = types.ModuleType('django')
        fake_conf = types.ModuleType('django.conf')
        fake_conf.settings = settings
        fake_django.conf = fake_conf
        fake_openai = types.ModuleType('openai')
        fake_openai.OpenAI = FakeOpenAI
        fake_openai.AuthenticationError = FakeAuthenticationError
        with patch.dict(sys.modules, {
            'django': fake_django,
            'django.conf': fake_conf,
            'openai': fake_openai,
        }), patch.dict(os.environ, {'OPENAI_API_KEY': 'test-openai-key'}):
            spec = importlib.util.spec_from_file_location('rag_engine_under_test', ENGINE_PATH)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            self.engine = module.ChromaEngine()

    def test_generates_answer_with_gpt_6_sol(self):
        self.engine._build_messages = lambda question: [{'role': 'user', 'content': question}]
        self.assertEqual(self.engine.query('如何校准？'), '你好，世界')
        self.assertIsNone(self.engine.client.base_url)
        self.assertEqual(self.engine.client.responses.last_request['model'], 'gpt-6-sol')
        self.assertEqual(self.engine.client.responses.last_request['reasoning'], {'effort': 'high'})
        self.assertIs(self.engine.client.responses.last_request['store'], False)

    def test_custom_api_base_url_routes_answer_to_relay(self):
        self.settings.OPENAI_BASE_URL = 'https://api.example.com/v1'
        engine = self.engine.__class__()
        engine._build_messages = lambda question: [{'role': 'user', 'content': question}]
        self.assertEqual(engine.query('如何校准？'), '你好，世界')
        self.assertEqual(engine.client.base_url, 'https://api.example.com/v1')

    def test_streams_text_deltas(self):
        self.engine._build_messages = lambda question: [{'role': 'user', 'content': question}]
        self.assertEqual(list(self.engine.query_stream('如何校准？')), ['你好', '，世界'])
        self.assertEqual(self.engine.client.responses.last_request['reasoning'], {'effort': 'high'})
        self.assertIs(self.engine.client.responses.last_request['store'], False)
        self.assertIs(self.engine.client.responses.last_request['stream'], True)

    def test_embeds_documents_in_original_order(self):
        self.assertEqual(self.engine._embed(['文档一', '文档二']), [[1.0], [2.0]])
        self.assertEqual(self.engine.client.embeddings.last_request['model'], 'text-embedding-3-small')
        self.assertEqual(self.engine.client.embeddings.last_request['dimensions'], 1024)

    def test_missing_key_error_does_not_show_environment_variable_name(self):
        self.settings.OPENAI_API_KEY = ''
        with patch.dict(os.environ, {'OPENAI_API_KEY': ''}):
            with self.assertRaises(RuntimeError) as error:
                self.engine.__class__()
        self.assertIn('问答服务未配置', str(error.exception))
        self.assertNotIn('OPENAI_API_KEY', str(error.exception))

    def test_invalid_openai_key_is_reported_without_key_fragment(self):
        self.engine._build_messages = lambda question: [{'role': 'user', 'content': question}]
        self.engine.client.responses.error = FakeAuthenticationError('Incorrect API key provided: sk-secret-fragment')
        with self.assertRaises(RuntimeError) as error:
            self.engine.query('如何校准？')
        self.assertIn('API 密钥无效或接口地址不匹配', str(error.exception))
        self.assertNotIn('sk-secret-fragment', str(error.exception))
        with self.assertRaises(RuntimeError) as stream_error:
            list(self.engine.query_stream('如何校准？'))
        self.assertNotIn('sk-secret-fragment', str(stream_error.exception))


if __name__ == '__main__':
    unittest.main()
