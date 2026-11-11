import {test} from 'node:test';
import assert from 'node:assert/strict';
import {parseHTML} from 'linkedom';
import '../browser-extension/parser.js';
const parser=globalThis.KejiBlackboard;
const doc=(html)=>parseHTML(html).document;
const url='https://course.pku.edu.cn/webapps/blackboard/content/listContent.jsp?course_id=_1_1&content_id=_10_1';
const shell=(html)=>`<div id="breadcrumbs"><a href="/webapps/blackboard/execute/courseMain?course_id=_1_1">测试课程</a></div><div id="courseMenuPalette_contents"><a href="${url}">课程作业</a></div><div id="content">${html}</div>`;

test('discovers only current course links and rejects expired login',()=>{
 assert.equal(parser.documentInfo(doc(shell('')),url).id,'_1_1');
 assert.throws(()=>parser.documentInfo(doc('<input type="password">'),url),/登录/);
 assert.throws(()=>parser.safeUrl('https://iaaa.pku.edu.cn/login'),/不属于/);
 assert.throws(()=>parser.safeUrl(url+'&token=abc'),/认证/);
});
test('reads attachment directory and requirements without scripts or input values',()=>{
 const d=doc(shell('<ul id="content_listContainer"><li id="contentListItem:_30_1"><h3>第1讲</h3><div class="details"><input value="PRIVATE"><script>SECRET</script><div class="vtbegenerated">课堂说明</div><ul class="attachments"><li><a href="/bbcswebdav/pid-30/xid-5">课件.pdf</a></li></ul></div></li></ul>'));
 const rows=parser.list(d,url,'courseware');
 assert.equal(rows[0].id,'_30_1');assert.equal(rows[0].text,'课堂说明');assert.equal(rows[0].attachments[0].title,'课件.pdf');
 assert.ok(!JSON.stringify(rows).includes('PRIVATE'));assert.ok(!JSON.stringify(rows).includes('SECRET'));
});
test('empty notices are distinguished from unexpected structure',()=>{
 assert.deepEqual(parser.notices(doc(shell('<h1>公告</h1>'))),[]);
 assert.throws(()=>parser.notices(doc(shell('<h1>错误</h1>'))),/不可识别/);
 assert.equal(parser.notices(doc(shell('<ul id="announcementList"><li id="_4_1"><h3>通知一</h3><div class="vtbegenerated">正文</div></li></ul>')))[0].text,'正文');
});
test('reads only assignment metadata, never submission fields or scores',()=>{
 const d=doc('<div id="metadata"><div class="metaSection"><div class="metaLabel">到期日期</div><div class="metaField">2026年11月24日 星期二 下午11:59</div></div></div><li id="instructions">作业要求</li><div id="step2">PRIVATE ANSWER</div><input type="hidden" value="nonce">');
 const info=parser.assignmentDetail(d);assert.equal(info.instructions,'作业要求');assert.ok(!JSON.stringify(info).includes('PRIVATE'));assert.ok(!JSON.stringify(info).includes('nonce'));
 assert.equal(parser.dates(info.systemDue,2026,'系统')[0].due,'2026-11-24T23:59:00+08:00');
});
test('detects conflicts, preserves both sources and selects earlier reminder',()=>{
 const item={text:'按时提交截止日期11月19日23：30。'};
 const info=parser.resolveDue(item,{systemDue:'2026年11月26日 下午11:30'},2026);
 assert.equal(info.conflict,true);assert.equal(info.due,'2026-11-19T23:30:00+08:00');assert.equal(info.evidence.length,2);
 assert.equal(parser.resolveDue({text:'截止另行通知'},null,2026).due,null);
 assert.deepEqual(parser.dates('2026年2月30日晚23:59',2026,'正文'),[]);
});
test('stable locators omit collection timestamp so re-collecting is idempotent',()=>{
 const page={url,items:[]};
 const pages={notices:{...page,items:[{id:'_n_1',title:'通知',text:'内容'}]},assignments:{...page,items:[{id:'_a_1',title:'作业',url,text:'11月19日23:30',attachments:[]}]},courseware:{...page,items:[]}};
 const a=parser.bundle({id:'_1_1',name:'测试'},pages,'2026-11-11T00:00:00Z');
 const b=parser.bundle({id:'_1_1',name:'测试'},pages,'2026-11-11T01:00:00Z');
 assert.deepEqual(a.materials,b.materials);assert.deepEqual(a.deadlines,b.deadlines);assert.equal(a.collection.sections.notices.count,1);
});

test('collector walks three sections and nested folders using GET only',async()=>{
 const vm=await import('node:vm');const fs=await import('node:fs/promises');
 const current='https://course.pku.edu.cn/webapps/blackboard/content/listContent.jsp?course_id=_1_1&content_id=_10_1';
 const urls={notices:'https://course.pku.edu.cn/notices?course_id=_1_1',assignments:'https://course.pku.edu.cn/assignments?course_id=_1_1',courseware:'https://course.pku.edu.cn/courseware?course_id=_1_1',info:'https://course.pku.edu.cn/info?course_id=_1_1',folder:'https://course.pku.edu.cn/webapps/blackboard/content/listContent.jsp?course_id=_1_1&content_id=_20_1',detail:'https://course.pku.edu.cn/webapps/assignment/uploadAssignment?course_id=_1_1&content_id=_30_1'};
 const menu=`<div id="courseMenuPalette_contents"><a href="${urls.notices}">课程通知</a><a href="${urls.assignments}">课程作业</a><a href="${urls.courseware}">课程内容</a><a href="${urls.info}">课程信息</a></div>`;
 const wrap=(html)=>shell(html).replace(/<div id="courseMenuPalette_contents">.*?<\/div>/,menu);
 const pages={
  [urls.info]:wrap('<ul id="content_listContainer"><li id="contentListItem:_info_1"><h3>课程基本信息</h3><div class="vtbegenerated">时间：星期四7~8节（09:00~10:50） 地点：示例教室A</div></li></ul>'),
  [urls.notices]:wrap('<ul id="announcementList"><li id="_n_1"><h3>公告</h3><div class="vtbegenerated">新作业已发布</div></li></ul>'),
  [urls.assignments]:wrap(`<ul id="content_listContainer"><li id="contentListItem:_30_1"><h3><a href="${urls.detail}">作业</a></h3><div class="vtbegenerated">2026年11月19日23:30</div></li></ul>`),
  [urls.detail]:wrap('<li id="metadata"><div class="metaSection"><div class="metaLabel">到期日期</div><div class="metaField">2026年11月19日 下午11:30</div></div></li><li id="instructions">请作答</li><div id="step2"><input value="PRIVATE ANSWER"></div>'),
  [urls.courseware]:wrap(`<ul id="content_listContainer"><li id="contentListItem:_folder_1"><h3><a href="${urls.folder}">第一章</a></h3></li></ul>`),
  [urls.folder]:wrap('<ul id="content_listContainer"><li id="contentListItem:_slide_1"><h3>课件</h3><div class="vtbegenerated">课件目录</div><ul class="attachments"><li><a href="/bbcswebdav/xid-5">讲义.pdf</a></li></ul></li></ul>')
 };
 const calls=[];
 const context={document:doc(wrap('')),location:{href:current},globalThis:{KejiBlackboard:parser},URL,DOMParser:class{parseFromString(html){return doc(html);}},AbortSignal,Date,
  fetch:async(target,options)=>{calls.push({target,options});assert.ok(pages[target],target);return {ok:true,url:target,text:async()=>pages[target]};}};
 const result=await vm.runInNewContext(await fs.readFile(new URL('../browser-extension/collector.js',import.meta.url),'utf8'),context);
 assert.equal(result.materials.length,3);assert.equal(result.deadlines.length,1);assert.equal(result.collection.sections.courseware.count,1);
 assert.equal(result.materials.find(x=>x.category==='课件目录').attachments[0].title,'讲义.pdf');
 assert.equal(result.schedules.length,1);assert.equal(result.collection.timetable.status,'found');assert.equal(calls.length,6);assert.ok(calls.every(x=>!x.options.method && x.options.credentials==='same-origin'));assert.ok(!JSON.stringify(result).includes('PRIVATE'));
 // A failed HTTP section must reject the whole snapshot rather than report an empty directory.
 context.fetch=async()=>({ok:false,status:503});
 await assert.rejects(vm.runInNewContext(await fs.readFile(new URL('../browser-extension/collector.js',import.meta.url),'utf8'),context),/503/);
});

test('assessment description date is read without an attempt action',()=>{
 const d=doc('<div id="stepcontent1">到期日期 该 Test 将于 2026年11月26日 下午11时30分00秒 CST 截止。<button>开始</button></div><div id="step2">PRIVATE</div>');
 const detail=parser.assignmentDetail(d,true);
 assert.equal(parser.dates(detail.systemDue,2026,'系统')[0].due,'2026-11-26T23:30:00+08:00');
 assert.ok(!JSON.stringify(detail).includes('PRIVATE'));
});


test('timetable parses explicit class hours and excludes office hours',()=>{
 const page=doc(shell('<ul id="content_listContainer"><li id="contentListItem:_info_1"><h3>课程基本信息</h3><div class="vtbegenerated">时间：星期四7~8节（09:00~10:50）\n地点：示例教室A\noffice time：周五下午14:00~10:50，理科1号楼1530E</div></li></ul>'));
 const result=parser.timetable(page,url);
 assert.equal(result.status,'found');assert.equal(result.items.length,1);
 assert.deepEqual([result.items[0].weekday,result.items[0].startTime,result.items[0].endTime,result.items[0].location],[4,'09:00','10:50','示例教室A']);
 assert.ok(result.items[0].note.includes('未明确教学周次'));
 const unknown=doc(shell('<ul id="content_listContainer"><li id="contentListItem:_info_1"><h3>课程基本信息</h3><div class="vtbegenerated">office time：周五14:00~10:50</div></li></ul>'));
 assert.equal(parser.timetable(unknown,url).status,'unrecognized');
 assert.equal(parser.timetable(unknown,url).items.length,0);
});
