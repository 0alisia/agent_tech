"""Import the starter knowledge library without changing user-edited documents."""

import argparse
import json
import sqlite3
from contextlib import closing
from datetime import datetime, timedelta, timezone
from pathlib import Path


DEFAULT_DATABASE = Path(__file__).resolve().parents[1] / 'db.sqlite3'
DEFAULT_DATA = Path(__file__).with_name('knowledge_docs.json')


def seed_docs(database=DEFAULT_DATABASE, data_file=DEFAULT_DATA):
    documents = json.loads(Path(data_file).read_text(encoding='utf-8'))
    if len({doc['title'] for doc in documents}) != len(documents):
        raise ValueError('文档标题重复')

    inserted = 0
    import_time = datetime.now(timezone.utc)
    with closing(sqlite3.connect(database)) as connection, connection:
        for doc in reversed(documents):
            if connection.execute(
                'SELECT 1 FROM drones_dronedoc WHERE title = ? LIMIT 1',
                (doc['title'],),
            ).fetchone():
                continue
            now = (import_time + timedelta(microseconds=inserted)).strftime('%Y-%m-%d %H:%M:%S.%f')
            connection.execute(
                'INSERT INTO drones_dronedoc '
                '(title, model_name, category, tags, content, created_at, updated_at) '
                'VALUES (?, ?, ?, ?, ?, ?, ?)',
                (doc['title'], doc['model_name'], doc['category'], doc['tags'], doc['content'], now, now),
            )
            inserted += 1
    return inserted


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--database', type=Path, default=DEFAULT_DATABASE)
    parser.add_argument('--data', type=Path, default=DEFAULT_DATA)
    args = parser.parse_args()
    print(f'新增 {seed_docs(args.database, args.data)} 篇知识文档')
