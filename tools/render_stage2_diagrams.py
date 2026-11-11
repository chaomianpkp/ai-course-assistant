"""Editable SVG companion figures for Mermaid sources; no browser required."""
from pathlib import Path
from html import escape

OUT = Path(__file__).resolve().parents[1] / 'docs/stage2/diagrams'
class Figure:
    def __init__(self, title, subtitle='', w=1500, h=900):
        self.w,self.h=w,h
        self.parts=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}"><defs><marker id="arrow" markerWidth="10" markerHeight="8" refX="9" refY="4" orient="auto"><path d="M0,0 L9,4 L0,8" fill="none" stroke="#34483d" stroke-width="1.5"/></marker></defs><rect width="100%" height="100%" fill="#fffdf8"/>']
        self.text(55,55,title,30,anchor='start')
        self.text(55,88,subtitle,19,anchor='start',color='#6f675c')
    def text(self,x,y,t,size=20,anchor='middle',color='#263c31'):
        for i,line in enumerate(t.split('\n')):
            self.parts.append(f'<text x="{x}" y="{y+i*(size+8)}" text-anchor="{anchor}" font-family="Times New Roman,Songti SC,serif" font-size="{size}" fill="{color}">{escape(line)}</text>')
    def box(self,x,y,w,h,title,body='',ellipse=False):
        if ellipse:self.parts.append(f'<ellipse cx="{x+w/2}" cy="{y+h/2}" rx="{w/2}" ry="{h/2}" fill="#f0f5ef" stroke="#34483d" stroke-width="2"/>')
        else:self.parts.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="3" fill="#f0f5ef" stroke="#34483d" stroke-width="2"/>')
        if body:
            self.text(x+w/2,y+32,title,23)
            self.parts.append(f'<path d="M{x},{y+48} H{x+w}" stroke="#34483d"/>')
            self.text(x+15,y+77,body,19,anchor='start')
        else:self.text(x+w/2,y+h/2+7,title,22)
    def line(self,x1,y1,x2,y2,label='',arrow=False,dash=False):
        self.parts.append(f'<path d="M{x1},{y1} L{x2},{y2}" fill="none" stroke="#34483d" stroke-width="2"'+(' stroke-dasharray="8 5"' if dash else '')+(' marker-end="url(#arrow)"' if arrow else '')+'/>')
        if label:self.text((x1+x2)/2+8,(y1+y2)/2-9,label,18)
    def save(self,name):
        (OUT/(name+'.svg')).write_text(''.join(self.parts)+'</svg>')

f=Figure('用况图：课程资料收集与作业辅导','学生用矩形文字框表示；作业辅导为第二阶段设计，未接入生成服务')
f.parts.append('<rect x="340" y="130" width="1080" height="690" fill="none" stroke="#34483d" stroke-width="2"/>')
f.text(880,165,'课迹系统',24)
f.box(65,440,180,90,'学生')
for i,title in enumerate(['导入教学网课程','检索与追溯版本','查看课表与标记截止','申请辅导草稿','核对引用并确认']):
 y=195+i*115
 f.box(520,y,370,80,title,ellipse=True)
 f.line(245,485,520,y+40)
f.box(1020,195,330,80,'校验来源与字段',ellipse=True)
f.line(890,235,1020,235,'«include»',True,True)
f.save('use-cases')

f=Figure('领域类图：课程资料收集','1对多关系标明数量；领域概念在当前实现中映射为数据记录与独立仓储')
for args in [(60,170,300,150,'Course','id / name'),(600,170,320,150,'Material','id / title / category'),(1110,170,320,150,'MaterialVersion','version / content\nrecordedAt'),(60,570,300,150,'Deadline','id / title / due'),(600,570,320,150,'SourceRef','url / title / locator'),(1110,570,320,150,'Completion','recordId / done')]:f.box(*args)
f.line(360,240,600,240,'1 收录 0..*')
f.line(920,240,1110,240,'1 组成 1..*')
f.line(210,320,210,570,'1 归属 0..*')
f.line(1270,320,1270,470)
f.line(1270,470,760,470,'多版本 → 1来源')
f.line(760,470,760,570,arrow=True)
f.line(360,645,600,645,'0..* 依据 1',True)
f.line(210,720,210,770)
f.line(210,770,1270,770,'1 截止项 → 0..1 完成状态')
f.line(1270,770,1270,720,arrow=True)
f.parts.append('<polygon points="920,240 932,233 944,240 932,247" fill="#34483d"/>')
f.text(1050,380,'SourceRef 随每个版本保存',19)
f.text(1050,410,'历史内容与完成状态分离',19)
f.text(750,815,'ImportBatch 记录批次计数；一次导入以数据库事务为边界',22)
f.save('collection-classes')

f=Figure('领域类图：作业辅导','规划设计；AI不持有审核记录或教学网提交权限')
for args in [(60,170,300,150,'Assignment','id / requirement\nsource'),(600,170,320,150,'GuidanceJob','id / status\ncontextVersion'),(1110,170,320,150,'ContextSnapshot','id\nmaterialVersionIds'),(60,570,300,150,'ReviewRecord','draftId / decision\nrecordedAt'),(600,570,320,150,'Draft','id / status'),(1110,570,320,150,'DraftSection','body / citations')]:f.box(*args)
f.line(360,240,600,240,'1 请求 0..*')
f.line(920,240,1110,240,'1 固定 1',True)
f.line(760,320,760,570,'1 产出 0..1',True)
f.line(600,645,360,645,'1 接受 0..*')
f.line(920,645,1110,645,'1 组成 1..*')
f.parts.append('<polygon points="920,645 932,638 944,645 932,652" fill="#34483d"/>')
f.line(1270,570,1270,320,'引用快照',True,True)
f.text(750,815,'主动对象 GuidanceWorker 领取并处理任务；学生确认后形成 ReviewRecord',22)
f.save('guidance-classes')

def sequence(name,title,subtitle,participants,messages):
 f=Figure(title,subtitle,h=1140)
 xs=[100+i*(1300/(len(participants)-1)) for i in range(len(participants))]
 for x,p in zip(xs,participants):
  f.box(x-85,125,170,65,p)
  f.line(x,190,x,1090,dash=True)
 for i,(a,b,t,reply) in enumerate(messages):
  y=245+i*70
  if a==b:
   x=xs[a];f.parts.append(f'<path d="M{x},{y} h50 v25 h-50" fill="none" stroke="#34483d" marker-end="url(#arrow)"/>');f.text(x+60,y+16,t,18,anchor='start')
  else:f.line(xs[a],y,xs[b],y,t,True,reply)
 f.save(name)
sequence('import-sequence','顺序图：资料导入','非法批次在写入前拒绝；保存过程以单事务完成',['学生','资料页','HTTP控制器','CourseImport','Repository'],[(0,1,'确认输入',False),(1,2,'POST /api/imports',False),(2,3,'parse(body)',False),(3,2,'校验通过；非法则400返回',True),(2,4,'save_import(bundle)',False),(4,2,'提交后返回新增/更新/未变化数',True),(2,1,'200 + 计数',True),(1,2,'GET /api/catalog',False),(2,4,'catalog()',False),(4,2,'返回持久化资料与截止',True),(2,1,'200 + 课程目录',True)])
sequence('guidance-sequence','顺序图：作业辅导','规划；启动任务和完成通知为异步，生成结果必须再校验',['学生','作业页','Controller','Worker','Generator'],[(0,1,'确认题目与材料范围',False),(1,2,'POST guidance-jobs',False),(2,1,'202 + jobId；固定快照',True),(2,3,'异步通知任务就绪',True),(3,4,'生成草稿请求（受限材料）',False),(4,3,'候选草稿或缺口说明',True),(3,2,'校验引用后保存任务结果',True),(1,2,'轮询GET job',False),(2,1,'待确认/资料不足/失败',True),(0,1,'核对后确认或退回',False),(1,2,'PATCH 人工审核记录',False)])

f=Figure('状态图：导入批次','当前实现的请求级状态；未保存临时校验过程为数据库记录')
for args in [(60,350,230,90,'待导入'),(420,350,240,90,'校验中'),(800,350,240,90,'事务保存中'),(1190,350,230,90,'完成'),(420,650,240,90,'不合法'),(800,650,240,90,'保存失败')]:f.box(*args)
f.line(290,395,420,395,'确认',True);f.line(660,395,800,395,'通过',True);f.line(1040,395,1190,395,'提交',True)
f.line(540,440,540,650,'非法',True);f.line(920,440,920,650,'回滚',True)
f.line(540,740,540,790)
f.line(540,790,175,790,'修改后重试')
f.line(175,790,175,440,arrow=True)
f.line(920,740,920,840)
f.line(920,840,120,840,'重试')
f.line(120,840,120,440,arrow=True)
f.line(1305,350,1305,190)
f.line(1305,190,175,190,'继续导入')
f.line(175,190,175,350,arrow=True)
f.parts.append('<circle cx="35" cy="395" r="10" fill="#34483d"/>')
f.line(45,395,60,395,arrow=True)
f.save('import-state')
f=Figure('状态图：辅导任务与草稿','规划；生成结果必须校验，确认与退回由学生触发')
for args in [(60,350,230,90,'排队'),(420,350,240,90,'生成中'),(800,350,240,90,'待人工确认'),(1190,350,230,90,'已确认'),(320,650,240,90,'资料不足'),(650,650,240,90,'失败'),(1000,650,240,90,'已退回')]:f.box(*args)
f.line(290,395,420,395,'领取',True);f.line(660,395,800,395,'校验通过',True);f.line(1040,395,1190,395,'学生确认',True)
f.line(500,440,440,650,'缺必要材料',True);f.line(620,440,770,650,'超时/非法结果',True);f.line(920,440,1120,650,'学生退回',True)
for x,y,label in [(440,780,'补材料后新请求'),(770,820,'失败后重试'),(1120,860,'修改要求后新请求')]:
 f.line(x,740,x,y);f.line(x,y,175,y,label);f.line(175,y,175,440,arrow=True)
f.parts.append('<circle cx="35" cy="395" r="10" fill="#34483d"/><circle cx="1460" cy="395" r="14" fill="none" stroke="#34483d" stroke-width="2"/><circle cx="1460" cy="395" r="9" fill="#34483d"/>')
f.line(45,395,60,395,arrow=True);f.line(1420,395,1446,395,arrow=True)
f.save('guidance-state')
f=Figure('包图：界面、控制、领域与数据','实线为已实现依赖；虚线为作业辅导规划依赖')
for args in [(60,180,380,120,'界面包','Vue看板 / 资料页'),(560,180,380,120,'控制包','server/app.py'),(1060,180,380,120,'领域包','CourseImport / 验证'),(560,540,380,120,'数据包','CourseRepository / SQLite'),(1060,540,380,120,'作业辅导包：计划','Controller / Worker / Generator')]:f.box(*args)
f.line(440,240,560,240,'HTTP',True);f.line(940,240,1060,240,'校验',True);f.line(750,300,750,540,'仓储调用',True)
f.line(1060,600,940,600,'资料快照',True,True);f.line(1250,540,1250,300,'输入校验',True,True)
f.text(750,810,'生成结果、学生审核与原始材料分开管理；本地单用户版本不开放网络部署',22)
f.save('packages')

f=Figure('教学网采集：浏览器到本机课迹','复用Chrome已登录会话；只读GET，不导出Cookie或提交作业')
for args in [(60,210,330,150,'Chrome当前课程','用户已登录\n用户点击采集'),(570,210,330,150,'Collector / Parser','发现资料与课程信息\n只读页面并解析'),(1080,210,330,150,'预览与确认','通知 / 作业 / 课件目录\n课表、冲突与待确认'),(570,600,330,150,'本机接收控制器','连接码 / 三栏目验证\n全批次校验与事务保存'),(1080,600,330,150,'看板与资料页','原始链接 / 附件目录\n版本历史 / 截止依据')]:f.box(*args)
f.line(390,285,570,285,'临时读取',True)
f.line(900,285,1080,285,'结构化快照',True)
f.line(1245,360,1245,490)
f.line(1245,490,735,490,'确认后POST')
f.line(735,490,735,600,arrow=True)
f.line(900,675,1080,675,'刷新GET',True)
f.text(750,830,'原始教学网页面保留在Chrome；本地库只保存课程内容和来源，不保存认证信息',21)
f.save('blackboard-import')

f=Figure('领域类图补充：课程课表','Schedule以原始来源定位生成稳定ID；不根据星期擅自推算教学日期')
f.box(60,300,330,200,'Course','id / name')
f.box(570,240,380,360,'Schedule','id / weekday / periods\nstartTime / endTime\nlocation / rawText / note\nversion / source')
f.box(1110,300,330,200,'SourceRef','url / title / locator')
f.line(390,390,570,390,'1 拥有 0..*',True)
f.line(950,390,1110,390,'0..* 依据 1',True)
f.text(750,730,'课程页未明确教学周次、起止日期、停调课时，显示待核对提示',24)
f.text(750,795,'上课安排与office time分开；重新采集不增加相同版本',23)
f.save('timetable-classes')
