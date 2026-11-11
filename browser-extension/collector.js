// Injected only after the student clicks the extension on a course page.
(async function () {
  const parser = globalThis.KejiBlackboard;
  const {id,name,nav} = parser.documentInfo(document, location.href);
  const choose=(names)=>nav.find(item=>names.includes(item.title))?.url;
  const roots={notices:choose(['课程通知']),assignments:choose(['课程作业']),courseware:choose(['教学内容','课程内容'])};
  if(Object.values(roots).some(url=>!url)) throw new Error('课程菜单缺少通知、作业或课程内容入口，暂不支持这门课');
  const fetchDoc=async(url)=>{
    parser.safeUrl(url);
    const target=new URL(url);
    if(target.searchParams.get('course_id') !== id) throw new Error('发现跨课程链接，已停止');
    const response=await fetch(url,{credentials:'same-origin',signal:AbortSignal.timeout(20000)});
    if(!response.ok) throw new Error(`教学网读取失败：HTTP ${response.status}`);
    parser.safeUrl(response.url);
    const doc=new DOMParser().parseFromString(await response.text(),'text/html');
    if(parser.documentInfo(doc,response.url).id !== id)throw new Error('读取结果跨课程，已停止');
    return {doc,url:response.url};
  };
  const pages={};
  for(const section of ['notices','assignments','courseware']) {
    const page=await fetchDoc(roots[section]);
    const items=section==='notices'?parser.notices(page.doc):parser.list(page.doc,page.url,section);
    pages[section]={url:page.url,items};
  }
  // Follow content folders only, bounded by 30 pages. Read failures abort instead of silently dropping a section.
  for(const section of ['assignments','courseware']) {
    const queue=pages[section].items.filter(i=>i.folder), seen=new Set([pages[section].url]);
    pages[section].items=pages[section].items.filter(i=>!i.folder);
    while(queue.length){
      const folder=queue.shift();if(seen.has(folder.url))continue;
      if(seen.size>=30)throw new Error('目录超过30页，请拆分后导入；本次未保存');
      seen.add(folder.url);
      const page=await fetchDoc(folder.url);
      for(const item of parser.list(page.doc,page.url,section)) {
        item.pageUrl=page.url;
        if(item.folder)queue.push(item); else pages[section].items.push(item);
      }
    }
  }
  pages.assignments.items=pages.assignments.items.filter(item=>item.assignment);
  for(const item of pages.assignments.items) {
    // GET details only. Never launch an attempt or call a save/submit endpoint.
    const url=new URL(item.url);
    if(url.pathname==='/webapps/assignment/uploadAssignment' || url.pathname==='/webapps/blackboard/content/launchAssessment.jsp') {
      const page=await fetchDoc(item.url);item.detail=parser.assignmentDetail(page.doc, item.assessment);
    }
    // Assessment description pages are GET-only; no start, attempt, answer or submit action is called.
  }
  const infoUrl=choose(['课程信息']);
  if(infoUrl){const page=await fetchDoc(infoUrl);pages.timetable=parser.timetable(page.doc,page.url);}
  const checkedAt=new Date().toISOString();
  return parser.bundle({id,name},pages,checkedAt);
})()
