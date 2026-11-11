import copy
import json
from pathlib import Path
import tempfile
import threading
import unittest
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from http.server import ThreadingHTTPServer
from server.app import handler_for
from server.domain import CourseImport, ValidationError
from server.repository import CourseRepository


def fixture():
    source = {'title': '课程作业页', 'url': 'https://course.pku.edu.cn/coursework', 'locator': '第二次作业'}
    return {'course': {'id': 'se', 'name': '软件工程'},
            'materials': [{'title': '第二次作业', 'category': '作业要求', 'content': '完成OOA分析与设计', 'source': source}],
            'deadlines': [{'title': '第二次作业', 'due': '2026-11-24T23:59:00+08:00', 'source': source}]}


class RepositoryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / 'test.sqlite3'
        self.repo = CourseRepository(self.path)

    def tearDown(self):
        self.temp.cleanup()

    def test_dedup_version_and_student_state_survive_restart(self):
        body = fixture()
        self.assertEqual(self.repo.save_import(CourseImport.parse(body))['inserted'], 2)
        deadline = self.repo.catalog()['deadlines'][0]
        self.repo.set_done(deadline['id'], True)
        self.assertEqual(self.repo.save_import(CourseImport.parse(body))['unchanged'], 2)
        body['materials'][0]['content'] = '更新后的要求'
        self.assertEqual(self.repo.save_import(CourseImport.parse(body))['updated'], 1)
        reopened = CourseRepository(self.path)
        self.assertTrue(reopened.catalog()['deadlines'][0]['done'])
        material = reopened.catalog()['materials'][0]
        self.assertEqual(material['version'], 2)
        self.assertEqual(reopened.history(material['id'])[1]['record']['content'], '完成OOA分析与设计')

    def test_invalid_last_item_does_not_partially_write(self):
        body = fixture()
        body['deadlines'][0]['due'] = '2026-11-24T23:59'
        with self.assertRaises(ValidationError):
            self.repo.save_import(CourseImport.parse(body))
        self.assertEqual(self.repo.catalog()['materials'], [])
        self.assertEqual(self.repo.catalog()['courses'], [])

    def test_database_failure_rolls_back_whole_import(self):
        import sqlite3
        bundle = CourseImport.parse(fixture())
        # Force a constraint failure after the first row, proving rollback.
        bundle.records[1]['id'] = None
        with self.repo.connect() as db:
            db.execute("CREATE TRIGGER reject_invalid BEFORE INSERT ON records WHEN NEW.id IS NULL BEGIN SELECT RAISE(ABORT, 'bad id'); END")
        with self.assertRaises(sqlite3.IntegrityError):
            self.repo.save_import(bundle)
        self.assertEqual(self.repo.catalog()['materials'], [])
        self.assertEqual(self.repo.catalog()['courses'], [])

    def test_source_urls_and_duplicates_rejected(self):
        for url in ['javascript:alert(1)', 'file:///etc/passwd', 'https://user:password@example.org/', 'https://example.org/?token=secret']:
            body = fixture()
            body['materials'][0]['source']['url'] = url
            with self.subTest(url=url), self.assertRaises(ValidationError):
                CourseImport.parse(body)
        body = fixture()
        body['materials'].append(copy.deepcopy(body['materials'][0]))
        with self.assertRaises(ValidationError): CourseImport.parse(body)

    def test_schedule_validation_versions_and_restart(self):
        body=fixture()
        row={'title':'上课安排','weekday':4,'startTime':'09:00','endTime':'10:50','periods':'7~8','location':'示例教室A','rawText':'时间：星期四7~8节（09:00~10:50） 地点：示例教室A','note':'周次待核对','source':{'url':'https://course.pku.edu.cn/info','title':'课程信息','locator':'schedule'}}
        body['schedules']=[row]
        self.assertEqual(self.repo.save_import(CourseImport.parse(body))['inserted'],3)
        self.assertEqual(self.repo.save_import(CourseImport.parse(body))['unchanged'],3)
        for field,value in [('weekday',True),('weekday',8),('startTime','25:00'),('endTime','08:00')]:
            invalid=copy.deepcopy(body);invalid['schedules'][0][field]=value
            with self.subTest(field=field,value=value),self.assertRaises(ValidationError): CourseImport.parse(invalid)
        row['location']='示例教室B'
        self.assertEqual(self.repo.save_import(CourseImport.parse(body))['updated'],1)
        reopened=CourseRepository(self.path);schedule=reopened.catalog()['schedules'][0]
        self.assertEqual(schedule['location'],'示例教室B')
        self.assertEqual(reopened.history(schedule['id'])[1]['record']['location'],'示例教室A')
        with self.assertRaises(KeyError):reopened.set_done(schedule['id'],True)

    def test_cannot_mark_a_material_as_done(self):
        self.repo.save_import(CourseImport.parse(fixture()))
        material = self.repo.catalog()['materials'][0]
        with self.assertRaises(KeyError): self.repo.set_done(material['id'], True)


class ApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.repo = CourseRepository(Path(cls.temp.name) / 'test.sqlite3')
        cls.server = ThreadingHTTPServer(('127.0.0.1', 0), handler_for(cls.repo, Path(cls.temp.name)))
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.base = f'http://127.0.0.1:{cls.server.server_port}'

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown(); cls.server.server_close(); cls.thread.join(); cls.temp.cleanup()

    def request(self, path, data=None, method=None, headers=None):
        request = Request(self.base + path, data=json.dumps(data).encode() if data is not None else None,
                          method=method, headers=headers or {'Content-Type': 'application/json'})
        try:
            with urlopen(request) as result: return result.status, json.load(result)
        except HTTPError as e: return e.code, json.load(e)

    def test_api_import_read_and_complete(self):
        self.assertEqual(self.request('/api/imports', fixture(), 'POST')[0], 200)
        status, catalog = self.request('/api/catalog')
        self.assertEqual(status, 200)
        deadline = catalog['deadlines'][0]
        self.assertEqual(self.request('/api/deadlines/' + deadline['id'], {'done': True}, 'PATCH')[0], 200)
        self.assertTrue(self.request('/api/catalog')[1]['deadlines'][0]['done'])
        self.assertEqual(self.request('/api/deadlines/' + deadline['id'], {'done': 'false'}, 'PATCH')[0], 400)

    def test_reject_cross_origin_and_malformed_json(self):
        self.assertEqual(self.request('/api/imports', fixture(), 'POST', {'Content-Type': 'application/json', 'Origin': 'https://other.example'})[0], 400)
        self.assertEqual(self.request('/api/imports', fixture(), 'POST', {'Content-Type': 'text/plain'})[0], 400)
        self.assertEqual(self.request('/api/imports', [], 'POST')[0], 400)

    def test_extension_requires_live_pairing_code(self):
        self.assertEqual(self.request('/api/blackboard/imports', fixture(), 'POST', {'Content-Type':'application/json','Origin':'chrome-extension://test'})[0],400)
        key=self.request('/api/connector')[1]['pairingCode']
        self.assertEqual(self.request('/api/connector', headers={'Origin':'https://other.example'})[0],403)
        body={'course':{'id':'pku_1_1','name':'测试'},'materials':[], 'collection':{'provider':'pku-blackboard','courseKey':'_1_1','checkedAt':'2026-11-11T00:00:00Z','sections':{name:{'count':0,'url':'https://course.pku.edu.cn/content?course_id=_1_1'} for name in ['notices','assignments','courseware']}}}
        headers={'Content-Type':'application/json','Origin':'chrome-extension://test','X-Keji-Key':key}
        self.assertEqual(self.request('/api/blackboard/imports',body,'POST',headers)[0],200)
        catalog=self.request('/api/catalog')[1]
        self.assertEqual(catalog['collections'][0]['sections']['notices']['count'],0)
        body['schedules']=[{'title':'上课安排','weekday':4,'startTime':'09:00','endTime':'10:50','periods':'7~8','location':'示例教室A','rawText':'星期四7~8节','source':{'url':'https://course.pku.edu.cn/info?course_id=_1_1','title':'课程基本信息','locator':'_info_1'}}]
        body['collection']['timetable']={'status':'found','count':1,'url':'https://course.pku.edu.cn/info?course_id=_1_1'}
        self.assertEqual(self.request('/api/blackboard/imports',body,'POST',headers)[0],200)
        self.assertEqual(self.request('/api/catalog')[1]['schedules'][0]['location'],'示例教室A')
        invalid=copy.deepcopy(body);invalid['schedules'][0]['source']['url']='https://course.pku.edu.cn/info?course_id=_2_1'
        self.assertEqual(self.request('/api/blackboard/imports',invalid,'POST',headers)[0],400)
        invalid=copy.deepcopy(body);invalid['collection']['timetable']['count']=0
        self.assertEqual(self.request('/api/blackboard/imports',invalid,'POST',headers)[0],400)
        self.assertEqual(len(self.request('/api/catalog')[1]['schedules']),1)


    def test_no_path_traversal_or_unknown_api(self):
        self.assertEqual(self.request('/../server/app.py')[0], 404)
        self.assertEqual(self.request('/api/missing')[0], 404)

class BlackboardTests(unittest.TestCase):
    def test_snapshot_counts_and_source_course_must_match(self):
        from server.blackboard import validate_collection
        body = {'course': {'id':'pku_1_1','name':'测试课'},'materials':[], 'collection': {'provider':'pku-blackboard','courseKey':'_1_1','checkedAt':'2026-11-11T00:00:00Z','sections':{name:{'count':0,'url':'https://course.pku.edu.cn/content?course_id=_1_1'} for name in ['notices','assignments','courseware']}}}
        self.assertEqual(validate_collection(body)['sections']['notices']['count'],0)
        self.assertEqual(CourseImport.parse(body).records,[])
        body['collection']['sections']['notices']['count']=1
        with self.assertRaises(ValidationError):CourseImport.parse(body)
        body['collection']['sections']['notices']['count']=0
        body['collection']['sections']['assignments']['url']='https://course.pku.edu.cn/content?course_id=_2_1'
        with self.assertRaises(ValidationError):validate_collection(body)
