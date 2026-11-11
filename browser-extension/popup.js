let bundle = null;
const collect=document.getElementById('collect'),send=document.getElementById('send'),status=document.getElementById('status'),error=document.getElementById('error');
collect.addEventListener('click',async()=>{
  bundle=null;send.disabled=true;collect.disabled=true;error.textContent='';status.textContent='正在读取当前课程…请保持弹窗打开';
  try {
    const [tab]=await chrome.tabs.query({active:true,currentWindow:true});
    if(!tab?.url?.startsWith('https://course.pku.edu.cn/'))throw new Error('请先打开已登录的北大教学网课程页面');
    await chrome.scripting.executeScript({target:{tabId:tab.id},files:['parser.js']});
    const results=await chrome.scripting.executeScript({target:{tabId:tab.id},files:['collector.js']});
    bundle=results[0]?.result;
    if(!bundle?.collection)throw new Error('未取得完整采集结果，请检查登录或课程页面');
    const sections=bundle.collection.sections;
    const conflicts=bundle.materials.filter(x=>x.dueInfo?.conflict).length;
    const unknown=bundle.materials.filter(x=>x.category==='作业要求'&&!x.dueInfo?.due).length;
    status.textContent=`${bundle.course.name}\n通知 ${sections.notices.count} 条\n作业 ${sections.assignments.count} 项\n课件目录 ${sections.courseware.count} 项\n课表 ${bundle.schedules?.length || 0} 项${bundle.schedules?.length ? '' : '（未识别，待补充）'}\n截止冲突 ${conflicts} 项，截止待确认 ${unknown} 项\n来源：course.pku.edu.cn\n采集完成，尚未导入。`;
    send.disabled=false;
  }catch(e){status.textContent='采集未完成，本次未导入';error.textContent=e.message;}
  finally{collect.disabled=false;}
});
send.addEventListener('click',async()=>{
  if(!bundle)return;
  send.disabled=true;error.textContent='';
  try {
    const key=document.getElementById('key').value.trim();
    if(!key)throw new Error('请填写本地课迹资料页显示的连接码');
    const response=await fetch('http://127.0.0.1:8765/api/blackboard/imports',{method:'POST',headers:{'Content-Type':'application/json','X-Keji-Key':key},body:JSON.stringify(bundle),signal:AbortSignal.timeout(15000)});
    const body=await response.json();if(!response.ok)throw new Error(body.error||'导入失败');
    status.textContent=`已导入：新增 ${body.inserted}，更新 ${body.updated}，未变化 ${body.unchanged}。\n回到课迹刷新，即可查看资料和截止。`;
  }catch(e){error.textContent=e.message==='Failed to fetch'?'无法连接本机课迹，请先启动本地服务。':e.message;}
  finally{send.disabled=false;}
});
