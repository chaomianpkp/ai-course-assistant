// 课程看板：课表、截止时间，以及日期文案。
export const courses = [
  {
    id: 'se',
    name: '软件工程',
    room: '理科一号楼 1131',
    weekday: 3,
    slot: '3–4 节',
    time: '10:10–12:00',
    accent: '#1e4d3a',
  },
  {
    id: 'os',
    name: '操作系统',
    room: '第二教学楼 201',
    weekday: 2,
    slot: '5–6 节',
    time: '14:00–15:50',
    accent: '#8a5a12',
  },
  {
    id: 'ds',
    name: '数据结构与算法',
    room: '理科二号楼 211',
    weekday: 4,
    slot: '1–2 节',
    time: '08:00–09:50',
    accent: '#24527a',
  },
]

export const deadlines = [
  {
    id: 'ds-hw3',
    courseId: 'ds',
    title: '第三次作业：图的遍历',
    due: '2026-10-09T22:00:00',
    source: '微信群「25秋数据结构」',
    sourceKind: '微信群',
  },
  {
    id: 'os-lab2',
    courseId: 'os',
    title: '实验二：进程调度',
    due: '2026-10-12T23:59:00',
    source: '课程网站实验页',
    sourceKind: '课程网站',
  },
  {
    id: 'se-srs',
    courseId: 'se',
    title: '需求规格说明书结构稿',
    due: '2026-10-15T23:59:00',
    source: '教学网作业区',
    sourceKind: '教学网',
  },
]

export const weekdays = [
  { id: 1, label: '周一' },
  { id: 2, label: '周二' },
  { id: 3, label: '周三' },
  { id: 4, label: '周四' },
  { id: 5, label: '周五' },
]

const weekdayNames = ['周日', '周一', '周二', '周三', '周四', '周五', '周六']

export function courseById(id) {
  return courses.find((course) => course.id === id)
}

export function formatDue(iso) {
  const date = new Date(iso)
  const hours = String(date.getHours()).padStart(2, '0')
  const minutes = String(date.getMinutes()).padStart(2, '0')
  return `${date.getMonth() + 1}月${date.getDate()}日 ${hours}:${minutes}`
}

export function dueLabel(iso, now = new Date()) {
  const due = new Date(iso)
  const start = Date.UTC(now.getFullYear(), now.getMonth(), now.getDate())
  const end = Date.UTC(due.getFullYear(), due.getMonth(), due.getDate())
  const days = Math.round((end - start) / 86400000)
  if (days < 0) return '已截止'
  if (days === 0) return '今天截止'
  if (days === 1) return '明天截止'
  return `还剩 ${days} 天`
}

export function formatToday(now = new Date()) {
  return `${now.getFullYear()}年${now.getMonth() + 1}月${now.getDate()}日 · ${weekdayNames[now.getDay()]}`
}

export function todayHeadline(now = new Date()) {
  const weekday = now.getDay()
  const todays = courses.filter((course) => course.weekday === weekday)
  if (todays.length) {
    const course = todays[0]
    const start = course.time.split('–')[0]
    return `今天${weekdayNames[weekday]}有课：${course.name} ${start}，${course.room}`
  }
  for (let offset = 1; offset <= 7; offset += 1) {
    const weekdayId = (weekday + offset) % 7
    const course = courses.find((item) => item.weekday === weekdayId)
    if (!course) continue
    const when = offset === 1 ? '明天' : weekdayNames[weekdayId]
    return `今天没有排课。下一门是${when}的${course.name}，${course.room}`
  }
  return '本周暂无课程'
}
