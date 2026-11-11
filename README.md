# 课迹

课程资料、截止与辅导的统一入口。第二阶段将资料收集和看板接入本地API与SQLite；回放、作业辅导、备考保留第一阶段原型，导航中已标明。

## 运行

需要 Node 20.19+/22.12+、Python 3.10+。后端仅使用Python标准库。

```sh
npm ci
npm run build
python3 server/app.py
```

打开 http://127.0.0.1:8765 。服务仅监听本机，数据库默认`.local-data/courses.sqlite3`，不入Git。

开发时分别运行`python3 server/app.py`和`npm run dev`，打开 http://127.0.0.1:5173 。API默认8765，Vite已配置代理；改变API端口时同步调整代理。

```sh
npm test
npm run build
```

## 可运行的资料流程

1. 打开“资料收集”，按教学网导入流程采集真实课程；也可填写文字或导入JSON清单。
2. 观察新增/更新/未变化计数；按课程、类型、关键词检索；打开原始来源、查看历史版本。
3. 看板展示带时区的截止项，勾选状态刷新后仍保留。标记完成仅是本地记录，不代表已向教学网提交。

支持从Chrome已登录教学网课程采集通知、作业和课件目录。先由用户确认加载browser-extension扩展；在课迹资料页复制临时连接码，采集预览后导入。手动文字/JSON仍可补充。登录由学生完成，不导出Cookie，不下载附件正文，不解析PDF或调用模型。详见docs/stage2/blackboard-import.md。同一课程+来源URL+定位对应同一记录；内容变化新增版本，来源改变视为新记录。

## 目录

|目录/文件|用途|
|---|---|
|server/domain.py|批次与来源验证|
|server/repository.py|SQLite事务、去重、版本和学生状态|
|server/app.py|本地API和生产前端服务|
|src/composables/useCourseStore.js|前端API状态|
|src/views/MaterialsView.vue|真实资料导入、检索、版本|
|src/views/DashboardView.vue|真实课程看板|
|src/data/、其他功能页面|第一阶段预设演示内容|
|docs/stage2/|分析设计、图示、AI报告、进度和演示材料|
|features.md、architecture.md、gantt-tasks.md|来自feature/add-doc分支的原规划及阶段修订|

原看板/资料原型保留在`/demo/dashboard`和`/demo/materials`；`/test/hello`继续可用。

本地版本为单用户演示，不适合公网或多人使用。不要上传数据库、教学网认证信息或未经许可的课程全文。

## 按原甘特图补齐课表

课表采集、校验、来源追溯与看板展示已实现。实际课程信息由组内保留，公开分支使用合成示例；20项测试通过。

真实课程名称、时间地点、教学网页面截图、联调快照和含真实内容的汇报PPT未纳入公开PR，由组内单独保留。本公开分支中的课程信息均为示例；实际验收结论见组内材料。
