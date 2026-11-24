import json
import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path

from drones.seed_knowledge_docs import seed_docs


class SeedKnowledgeDocsTests(unittest.TestCase):
    def test_imports_missing_docs_without_overwriting_existing_edits(self):
        with tempfile.TemporaryDirectory() as tmp:
            database = Path(tmp) / 'test.sqlite3'
            data_file = Path(tmp) / 'docs.json'
            data_file.write_text(json.dumps([
                {'title': '甲', 'category': 'faq', 'model_name': '通用', 'tags': 'A', 'content': '初始内容'},
                {'title': '乙', 'category': 'debug', 'model_name': '通用', 'tags': 'B', 'content': '第二篇'},
            ], ensure_ascii=False), encoding='utf-8')
            with closing(sqlite3.connect(database)) as connection, connection:
                connection.execute('CREATE TABLE drones_dronedoc (id INTEGER PRIMARY KEY, title TEXT, model_name TEXT, category TEXT, tags TEXT, content TEXT, created_at TEXT, updated_at TEXT)')

            self.assertEqual(seed_docs(database, data_file), 2)
            with closing(sqlite3.connect(database)) as connection, connection:
                connection.execute("UPDATE drones_dronedoc SET content = '用户修改' WHERE title = '甲'")

            self.assertEqual(seed_docs(database, data_file), 0)
            with closing(sqlite3.connect(database)) as connection:
                rows = connection.execute('SELECT title, content FROM drones_dronedoc').fetchall()
            self.assertEqual(dict(rows), {'甲': '用户修改', '乙': '第二篇'})
            with closing(sqlite3.connect(database)) as connection:
                titles = [row[0] for row in connection.execute('SELECT title FROM drones_dronedoc ORDER BY created_at DESC')]
            self.assertEqual(titles, ['甲', '乙'])


if __name__ == '__main__':
    unittest.main()
