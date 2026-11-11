"""Validate a browser-collected snapshot; authentication never leaves Chrome."""
from datetime import datetime
from urllib.parse import urlsplit, parse_qs
from server.domain import ValidationError, text


def validate_collection(body):
    if not isinstance(body, dict):
        raise ValidationError('采集结果格式无效')
    raw = body.get('collection')
    if not isinstance(raw, dict) or raw.get('provider') != 'pku-blackboard':
        raise ValidationError('缺少教学网采集记录')
    course_key = text(raw, 'courseKey', 80)
    if body.get('course', {}).get('id') != 'pku' + course_key:
        raise ValidationError('课程编号与采集结果不一致')
    checked_at = text(raw, 'checkedAt', 80)
    try:
        stamp = datetime.fromisoformat(checked_at.replace('Z', '+00:00'))
        if stamp.tzinfo is None: raise ValueError()
    except ValueError:
        raise ValidationError('核查时间必须含时区')
    sections = raw.get('sections')
    if not isinstance(sections, dict) or set(sections) != {'notices', 'assignments', 'courseware'}:
        raise ValidationError('必须完整检查通知、作业和课件三个栏目')
    normalized = {}
    for name in ('notices', 'assignments', 'courseware'):
        section = sections[name]
        if not isinstance(section, dict) or type(section.get('count')) is not int or not 0 <= section['count'] <= 500:
            raise ValidationError('栏目计数无效')
        url = text(section, 'url', 2000)
        parsed = urlsplit(url)
        if parsed.scheme != 'https' or parsed.netloc != 'course.pku.edu.cn' or parse_qs(parsed.query).get('course_id') != [course_key]:
            raise ValidationError('栏目来源必须属于同一教学网课程')
        normalized[name] = {'count':section['count'], 'url':url}
    materials = body.get('materials', [])
    if not isinstance(materials,list): raise ValidationError('资料清单无效')
    for name, entry in normalized.items():
        count = sum(1 for row in materials if isinstance(row,dict) and isinstance(row.get('origin'),dict) and row['origin'].get('section')==name)
        if count != entry['count']: raise ValidationError('栏目计数与实际条目不一致')
    timetable = raw.get('timetable')
    extra = {}
    if timetable is not None:
        if not isinstance(timetable,dict) or timetable.get('status') not in ('found','unrecognized') or type(timetable.get('count')) is not int:
            raise ValidationError('课表采集状态无效')
        parsed=urlsplit(text(timetable,'url',2000))
        if parsed.scheme != 'https' or parsed.netloc != 'course.pku.edu.cn' or parse_qs(parsed.query).get('course_id') != [course_key]:
            raise ValidationError('课表来源必须属于同一课程')
        schedules=body.get('schedules',[])
        if timetable['count'] != len(schedules) or bool(schedules) != (timetable['status']=='found'):
            raise ValidationError('课表计数与采集状态不一致')
        for row in schedules:
            src=urlsplit(row['source']['url'])
            if src.scheme != 'https' or src.netloc != 'course.pku.edu.cn' or parse_qs(src.query).get('course_id') != [course_key]:
                raise ValidationError('课表条目来源必须属于同一课程')
        extra['timetable']={'status':timetable['status'],'count':timetable['count'],'url':timetable['url']}
    return dict(extra, **{'provider':'pku-blackboard','courseKey':course_key,'checkedAt':checked_at,'sections':normalized})
