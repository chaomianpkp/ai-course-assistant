"""Validated course imports. All input is checked before opening a transaction."""
from dataclasses import dataclass
from datetime import datetime
import hashlib
import json
import re
from urllib.parse import urlsplit


class ValidationError(ValueError):
    pass


def text(obj, key, maximum=500, optional=False):
    value = obj.get(key, '')
    if not isinstance(value, str) or (not optional and not value.strip()) or len(value) > maximum:
        raise ValidationError(f'{key} 必须为{maximum}字以内的有效文本')
    return value.strip()


def source_of(obj):
    source = obj.get('source')
    if not isinstance(source, dict):
        raise ValidationError('每条记录必须包含 source 来源')
    url = text(source, 'url', 2000)
    try:
        parsed = urlsplit(url)
        if parsed.scheme not in ('http', 'https') or not parsed.hostname or parsed.username or parsed.password:
            raise ValueError()
        if parsed.query and re.search(r'(token|password|cookie|secret|authorization|session|ticket)=', parsed.query, re.I):
            raise ValueError()
    except ValueError:
        raise ValidationError('来源必须为不含账号密码或认证令牌的 HTTP(S) 链接')
    return {'url': url, 'title': text(source, 'title'), 'locator': text(source, 'locator', optional=True)}


def stable_id(kind, course_id, source):
    key = json.dumps([kind, course_id, source['url'], source['locator']], ensure_ascii=False)
    return hashlib.sha256(key.encode()).hexdigest()[:24]


@dataclass(frozen=True)
class CourseImport:
    course: dict
    records: list
    collection: dict = None

    @classmethod
    def parse(cls, body):
        if not isinstance(body, dict):
            raise ValidationError('导入内容必须是 JSON 对象')
        raw = body.get('course')
        if not isinstance(raw, dict):
            raise ValidationError('缺少 course 课程信息')
        course = {'id': text(raw, 'id', 80), 'name': text(raw, 'name', 200)}
        if not re.fullmatch(r'[A-Za-z0-9_-]+', course['id']):
            raise ValidationError('课程 id 只能包含字母、数字、下划线或横线')
        result, seen = [], set()
        for kind, field in [('material', 'materials'), ('deadline', 'deadlines'), ('schedule', 'schedules')]:
            rows = body.get(field, [])
            if not isinstance(rows, list) or len(rows) > 500:
                raise ValidationError(f'{field} 必须为最多500条的列表')
            for row in rows:
                if not isinstance(row, dict):
                    raise ValidationError('资料/截止项必须是对象')
                source = source_of(row)
                record = {'kind': kind, 'courseId': course['id'], 'title': text(row, 'title'), 'source': source}
                record['id'] = stable_id(kind, course['id'], source)
                if record['id'] in seen:
                    raise ValidationError('同一批次中来源链接和定位相同的记录重复，请合并或填写不同定位')
                seen.add(record['id'])
                if kind == 'material':
                    record.update(content=text(row, 'content', 100000), category=text(row, 'category', 50))
                elif kind == 'schedule':
                    weekday = row.get('weekday')
                    if type(weekday) is not int or not 1 <= weekday <= 7:
                        raise ValidationError('上课星期必须为1至7')
                    start, end = text(row, 'startTime', 5), text(row, 'endTime', 5)
                    if not all(re.fullmatch(r'(?:[01][0-9]|2[0-3]):[0-5][0-9]', t) for t in (start,end)) or start >= end:
                        raise ValidationError('上课时间必须为有效HH:mm且结束晚于开始')
                    record.update(weekday=weekday, startTime=start, endTime=end, location=text(row,'location',200), periods=text(row,'periods',80,optional=True), rawText=text(row,'rawText',5000), note=text(row,'note',500,optional=True))
                else:
                    due = text(row, 'due', 80)
                    try:
                        parsed = datetime.fromisoformat(due.replace('Z', '+00:00'))
                        if parsed.tzinfo is None:
                            raise ValueError()
                    except ValueError:
                        raise ValidationError('截止时间必须含时区，例如 2026-11-24T23:59:00+08:00')
                    record['due'] = parsed.isoformat()
                if 'attachments' in row:
                    if not isinstance(row['attachments'], list) or len(row['attachments']) > 100:
                        raise ValidationError('附件目录无效')
                    record['attachments'] = []
                    for attachment in row['attachments']:
                        if not isinstance(attachment, dict): raise ValidationError('附件目录无效')
                        ref = source_of({'source':dict(attachment, locator='')})
                        record['attachments'].append({'title':ref['title'],'url':ref['url']})
                if 'origin' in row:
                    origin = row['origin']
                    if not isinstance(origin, dict) or origin.get('provider') != 'pku-blackboard' or origin.get('section') not in ('notices','assignments','courseware','courseinfo'):
                        raise ValidationError('教学网条目来源无效')
                    record['origin'] = {'provider':'pku-blackboard','section':origin['section'],'itemKey':text(origin,'itemKey',100)}
                if 'dueInfo' in row:
                    info = row['dueInfo']
                    if not isinstance(info,dict) or type(info.get('conflict')) is not bool or not isinstance(info.get('evidence'),list) or len(info['evidence']) > 20:
                        raise ValidationError('截止依据无效')
                    evidence=[]
                    for candidate in info['evidence']:
                        if not isinstance(candidate,dict): raise ValidationError('截止依据无效')
                        value=text(candidate,'due',80)
                        try:
                            if datetime.fromisoformat(value.replace('Z','+00:00')).tzinfo is None: raise ValueError()
                        except ValueError: raise ValidationError('截止依据缺少有效时区')
                        evidence.append({'due':value,'source':text(candidate,'source',100),'text':text(candidate,'text',500),'inferredYear':bool(candidate.get('inferredYear'))})
                    record['dueInfo']={'due':info.get('due'), 'conflict':info['conflict'],'note':text(info,'note',500,optional=True),'evidence':evidence}
                    if info.get('due') and info['due'] not in [v['due'] for v in evidence]: raise ValidationError('选用的截止不在来源依据内')
                result.append(record)
        collection = None
        if 'collection' in body:
            from server.blackboard import validate_collection
            collection = validate_collection(body)
        if not result and collection is None:
            raise ValidationError('至少导入一条资料、截止或课表项')
        return cls(course, result, collection)
