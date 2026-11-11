"""SQLite transaction boundary; content versions and student state are separate."""
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path
import json
import sqlite3


class CourseRepository:
    def __init__(self, path):
        self.path = str(path)
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with closing(self.connect()) as db, db:
            db.executescript('''
                CREATE TABLE IF NOT EXISTS courses (id TEXT PRIMARY KEY, name TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS records (
                    id TEXT PRIMARY KEY, course_id TEXT NOT NULL, kind TEXT NOT NULL,
                    data TEXT NOT NULL, version INTEGER NOT NULL, updated_at TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS history (
                    record_id TEXT NOT NULL, version INTEGER NOT NULL, data TEXT NOT NULL,
                    recorded_at TEXT NOT NULL, PRIMARY KEY(record_id, version));
                CREATE TABLE IF NOT EXISTS student_state (
                    record_id TEXT PRIMARY KEY, done INTEGER NOT NULL DEFAULT 0);
                CREATE TABLE IF NOT EXISTS course_sync (course_id TEXT PRIMARY KEY, data TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS imports (
                    id INTEGER PRIMARY KEY, created_at TEXT NOT NULL, summary TEXT NOT NULL);
            ''')

    def connect(self):
        db = sqlite3.connect(self.path, timeout=10)
        db.row_factory = sqlite3.Row
        return db

    def save_import(self, bundle):
        now = datetime.now(timezone.utc).isoformat()
        counts = {'inserted': 0, 'updated': 0, 'unchanged': 0}
        with closing(self.connect()) as db, db:
            db.execute('INSERT INTO courses VALUES (?,?) ON CONFLICT(id) DO UPDATE SET name=excluded.name',
                       (bundle.course['id'], bundle.course['name']))
            for record in bundle.records:
                encoded = json.dumps(record, ensure_ascii=False, sort_keys=True)
                old = db.execute('SELECT * FROM records WHERE id=?', (record['id'],)).fetchone()
                if old and old['data'] == encoded:
                    counts['unchanged'] += 1
                    continue
                version = old['version'] + 1 if old else 1
                counts['updated' if old else 'inserted'] += 1
                db.execute('INSERT INTO records VALUES (?,?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET data=excluded.data, version=excluded.version, updated_at=excluded.updated_at',
                           (record['id'], record['courseId'], record['kind'], encoded, version, now))
                db.execute('INSERT INTO history VALUES (?,?,?,?)', (record['id'], version, encoded, now))
            if bundle.collection is not None:
                db.execute('INSERT INTO course_sync VALUES (?,?) ON CONFLICT(course_id) DO UPDATE SET data=excluded.data', (bundle.course['id'], json.dumps(bundle.collection, ensure_ascii=False,sort_keys=True)))
            cursor = db.execute('INSERT INTO imports(created_at,summary) VALUES (?,?)', (now, json.dumps(counts)))
            return dict(counts, importId=cursor.lastrowid)

    def catalog(self):
        with closing(self.connect()) as db:
            records = []
            for row in db.execute('SELECT r.*, COALESCE(s.done,0) AS done FROM records r LEFT JOIN student_state s ON s.record_id=r.id ORDER BY r.updated_at DESC,r.id'):
                records.append(dict(json.loads(row['data']), version=row['version'], updatedAt=row['updated_at'], done=bool(row['done'])))
            return {'courses': [dict(r) for r in db.execute('SELECT * FROM courses ORDER BY name')],
                    'collections': [dict(json.loads(r['data']), courseId=r['course_id']) for r in db.execute('SELECT * FROM course_sync')],
                    'materials': [r for r in records if r['kind'] == 'material'],
                    'deadlines': [r for r in records if r['kind'] == 'deadline'],
                    'schedules': [r for r in records if r['kind'] == 'schedule']}

    def set_done(self, record_id, done):
        with closing(self.connect()) as db, db:
            row = db.execute("SELECT id FROM records WHERE id=? AND kind='deadline'", (record_id,)).fetchone()
            if not row:
                raise KeyError('截止项不存在')
            db.execute('INSERT INTO student_state VALUES (?,?) ON CONFLICT(record_id) DO UPDATE SET done=excluded.done', (record_id, int(done)))
        return {'id': record_id, 'done': done}

    def history(self, record_id):
        with closing(self.connect()) as db:
            return [dict(version=r['version'], recordedAt=r['recorded_at'], record=json.loads(r['data']))
                    for r in db.execute('SELECT * FROM history WHERE record_id=? ORDER BY version DESC', (record_id,))]
