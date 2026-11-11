/* Shared deterministic DOM parser. No cookies, form values, grades or network writes. */
(function (root) {
  const ORIGIN = 'https://course.pku.edu.cn';
  function clean(text) { return String(text || '').replace(/\u00a0/g, ' ').replace(/[ \t]+/g, ' ').replace(/\n\s*\n/g, '\n').trim(); }
  function safeUrl(value, base = ORIGIN) {
    const url = new URL(value, base);
    if (url.origin !== ORIGIN || url.username || url.password) throw new Error('链接不属于北大教学网');
    for (const key of url.searchParams.keys()) {
      if (/token|password|cookie|secret|authorization|session|ticket|nonce/i.test(key)) throw new Error('链接包含认证参数，已停止');
    }
    url.hash = '';
    return url.href;
  }
  function contentText(element) {
    if (!element) return '';
    const copy = element.cloneNode(true);
    copy.querySelectorAll('script,style,input,textarea,iframe,button,.contextMenuContainer,.hideme,.editmode').forEach(el => el.remove());
    // textContent also works for DOMParser documents, whose innerText is unavailable.
    return clean(copy.textContent);
  }
  function documentInfo(doc, url) {
    safeUrl(url);
    if (doc.querySelector('input[type="password"]') || /\/login\/?/.test(new URL(url).pathname) || !doc.querySelector('#content')) {
      throw new Error('教学网登录已失效或页面结构不可识别，请先在Chrome完成登录');
    }
    const nav = [...doc.querySelectorAll('#courseMenuPalette_contents a')].map(a => ({title: clean(a.textContent), url: safeUrl(a.getAttribute('href'), url)}));
    const courseLink = [...doc.querySelectorAll('#breadcrumbs a')].find(a => /courseMain/.test(a.getAttribute('href') || ''));
    const id = new URL(url).searchParams.get('course_id') || (courseLink && new URL(courseLink.getAttribute('href'), ORIGIN).searchParams.get('course_id'));
    if (!/^_\d+_1$/.test(id || '') || !courseLink) throw new Error('请打开具体课程页面后再采集');
    return {id, name: clean(courseLink.textContent), nav};
  }
  function attachments(item, base) {
    return [...item.querySelectorAll('.attachments a[href]')].filter(a => /\/bbcswebdav\/|\/courses\//.test(a.getAttribute('href') || '')).map(a => ({title: clean(a.textContent), url: safeUrl(a.getAttribute('href'), base)}));
  }
  function list(doc, url, section) {
    const container = doc.querySelector('#content_listContainer');
    if (!container) throw new Error(`${section}目录结构发生变化，未将读取失败当作空目录`);
    return [...container.children].filter(el => el.tagName === 'LI').map(item => {
      const heading = item.querySelector('h3');
      if (!heading) throw new Error('目录项缺少标题，已停止本次采集');
      const link = heading.querySelector('a[href]');
      return {id: item.id.replace('contentListItem:', ''), title: clean(heading.textContent), text: contentText(item.querySelector('.vtbegenerated') || item.querySelector('.details')), attachments: attachments(item, url),
        url: link ? safeUrl(link.getAttribute('href'), url) : url,
        folder: !!link && /listContent.jsp/.test(link.getAttribute('href') || ''),
        assignment: !!link && /uploadAssignment|launchAssessment.jsp/.test(link.getAttribute('href') || '') || /^(作业|测试)$/.test(item.querySelector('img.item_icon')?.getAttribute('alt') || ''),
        assessment: !!link && /launchAssessment.jsp/.test(link.getAttribute('href') || '')};
    });
  }
  function notices(doc) {
    const list = doc.querySelector('#announcementList');
    // Blackboard renders an empty course announcement view without the UL.
    if (!list) {
      const heading = clean(doc.querySelector('#pageTitleText')?.textContent || doc.querySelector('#content h1')?.textContent);
      if (heading !== '公告' || !doc.querySelector('#content')) throw new Error('通知页面结构不可识别');
      return [];
    }
    return [...list.children].filter(el => el.tagName === 'LI').map(item => {
      const heading = item.querySelector('h3');
      if (!heading || !item.id) throw new Error('通知项缺少稳定编号');
      return {id:item.id, title:clean(heading.textContent), text:contentText(item.querySelector('.vtbegenerated') || item), publishedText:clean(item.querySelector('.postedDate')?.textContent || '')};
    });
  }
  function assignmentDetail(doc, assessment = false) {
    // Never read #step2, submission text, comments, marks, or hidden form inputs.
    const due = [...doc.querySelectorAll('#metadata .metaSection')].find(el => /到期日期/.test(el.querySelector('.metaLabel')?.textContent || ''));
    const mainText = assessment ? contentText(doc.querySelector('#stepcontent1')) : '';
    const assessmentDue = /到期日期[\s\S]{0,80}?((?:20\d{2})年\d{1,2}月\d{1,2}日[\s\S]{0,35}?(?:\d{1,2}[:时]\d{1,2})(?:分)?)/.exec(mainText)?.[1] || '';
    return {systemDue: contentText(due?.querySelector('.metaField')) || assessmentDue, instructions:contentText(doc.querySelector('#instructions'))};
  }
  function dates(text, year, label) {
    const result = [];
    const normalized = clean(text).replace(/[：]/g, ':');
    const pattern = /(?:(20\d{2})年)?(\d{1,2})月(\d{1,2})日(?:\s*星期[一二三四五六日天])?\s*(凌晨|上午|中午|下午|晚上|晚)?\s*(\d{1,2})(?::|时)(\d{1,2})(?:分)?/g;
    for (const match of normalized.matchAll(pattern)) {
      let hour = Number(match[5]);
      if (/下午|晚上|晚/.test(match[4] || '') && hour < 12) hour += 12;
      if (/凌晨|上午/.test(match[4] || '') && hour === 12) hour = 0;
      const y = Number(match[1] || year), month=Number(match[2]), day=Number(match[3]), minute=Number(match[6]);
      const check = new Date(Date.UTC(y, month-1, day, hour, minute));
      if (hour > 23 || minute > 59 || check.getUTCMonth() !== month-1 || check.getUTCDate() !== day) continue;
      result.push({due:`${y}-${String(month).padStart(2,'0')}-${String(day).padStart(2,'0')}T${String(hour).padStart(2,'0')}:${String(minute).padStart(2,'0')}:00+08:00`, source:label, text:match[0], inferredYear:!match[1]});
    }
    return result;
  }
  function resolveDue(item, detail, year) {
    const system = dates(detail?.systemDue || '', year, '系统到期日期');
    const body = dates(item.text, year, '作业列表正文');
    const instruction = dates(detail?.instructions || '', year, '作业要求正文');
    const evidence = [...system,...body,...instruction].filter((v,i,a)=>a.findIndex(x=>x.due===v.due && x.source===v.source)===i);
    const unique = [...new Set(evidence.map(x=>x.due))];
    return {due:unique.sort()[0] || null, conflict:unique.length>1, evidence,
      note: unique.length>1 ? '截止时间有冲突，暂按最早时间提醒，请核对来源' : !unique.length ? '未识别到明确截止时间，待确认' : evidence.every(x=>x.inferredYear) ? `年份按采集日期${year}推定，请核对` : ''};
  }
  function timetable(doc, url) {
    const rows=list(doc,url,'courseinfo').filter(item=>/基本信息|上课|课程安排/.test(item.title));
    const items=[];
    for(const item of rows) {
      const time=/时间[：:]\s*(?:星期|周)([一二三四五六日天])\s*(?:第)?(\d{1,2}\s*[~～—–-]\s*\d{1,2})\s*节\s*[（(]\s*(\d{1,2}[:：]\d{2})\s*[~～—–-]\s*(\d{1,2}[:：]\d{2})\s*[）)]/.exec(item.text);
      const place=/地点[：:]\s*([^\n\r]*?)(?=\s*(?:office\s*time|办公|$))/i.exec(item.text);
      if(!time || !place?.[1]?.trim())continue;
      const normalize=value=>value.replace('：',':').padStart(5,'0');
      const startTime=normalize(time[3]),endTime=normalize(time[4]);
      if(![startTime,endTime].every(t=>/^(?:[01]\d|2[0-3]):[0-5]\d$/.test(t)) || startTime>=endTime)continue;
      items.push({title:'上课安排',weekday:({'一':1,'二':2,'三':3,'四':4,'五':5,'六':6,'日':7,'天':7})[time[1]],startTime,endTime,location:clean(place[1]),periods:time[2].replace(/\s/g,''),rawText:item.text,
        note:'课程页未明确教学周次、起止日期或停调课安排，请结合校历和最新通知核对',source:{url:safeUrl(url),title:'课程信息 · '+item.title,locator:item.id},origin:{provider:'pku-blackboard',section:'courseinfo',itemKey:item.id}});
    }
    return {status:items.length?'found':'unrecognized',items,url:safeUrl(url)};
  }
  function bundle(course, pages, checkedAt) {
    const materials=[], deadlines=[], year=Number(checkedAt.slice(0,4));
    const source=(url,title,locator)=>({url:safeUrl(url),title,locator});
    for(const item of pages.notices.items) materials.push({title:item.title, category:'课程通知', content:item.text || item.title,
      source:source(pages.notices.url,course.name+' · 课程通知',item.id), origin:{provider:'pku-blackboard',section:'notices',itemKey:item.id}, attachments:[]});
    for(const item of pages.assignments.items) {
      const dueInfo=resolveDue(item,item.detail,year);
      const src=source(item.url,course.name+' · 课程作业',item.id);
      materials.push({title:item.title, category:'作业要求', content:item.text || '作业要求请打开原始页面核对。', source:src,
        origin:{provider:'pku-blackboard',section:'assignments',itemKey:item.id}, attachments:item.attachments, dueInfo});
      if(dueInfo.due) deadlines.push({title:item.title,due:dueInfo.due,source:src,dueInfo,origin:{provider:'pku-blackboard',section:'assignments',itemKey:item.id}});
    }
    for(const item of pages.courseware.items) materials.push({title:item.title, category:'课件目录', content:item.text || (item.attachments.length ? `已发布${item.attachments.length}个附件，目录链接见下方。` : '本课次未见附件。'),
      source:source(item.pageUrl || pages.courseware.url,course.name+' · 课程内容',item.id), origin:{provider:'pku-blackboard',section:'courseware',itemKey:item.id}, attachments:item.attachments});
    return {course:{id:'pku'+course.id,name:course.name},materials,deadlines,schedules:pages.timetable?.items || [],
      collection:{provider:'pku-blackboard',checkedAt,courseKey:course.id,timetable:pages.timetable?{status:pages.timetable.status,count:pages.timetable.items.length,url:pages.timetable.url}:undefined,sections:{notices:{count:pages.notices.items.length,url:pages.notices.url},assignments:{count:pages.assignments.items.length,url:pages.assignments.url},courseware:{count:pages.courseware.items.length,url:pages.courseware.url}}}};
  }
  const api={clean,safeUrl,documentInfo,list,notices,assignmentDetail,dates,resolveDue,timetable,bundle};
  root.KejiBlackboard=api;
  if(typeof module !== 'undefined') module.exports=api;
})(typeof globalThis !== 'undefined' ? globalThis : window);
