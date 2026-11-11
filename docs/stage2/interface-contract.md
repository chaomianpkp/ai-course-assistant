# 技能入口与接口约定（第二阶段定稿）

第二阶段让一门课的课表、截止与课件出现在看板和资料页。回放、作业辅导及备考的CLI任务按原甘特图在后续阶段实现，本阶段固定其入口和协议。

## 当前可运行接口

|方法与路径|输入/返回|作用|
|---|---|---|
|GET /api/health|服务状态|启动检查|
|GET /api/catalog|courses/materials/deadlines/schedules/collections|看板和资料页只读数据|
|GET /api/connector|内存临时连接码|连接本机Chrome采集助手|
|POST /api/blackboard/imports|教学网快照；inserted/updated/unchanged|仅保存用户确认的采集结果，不启动智能体|
|POST /api/imports|带来源的人工补充清单；同上计数|文字/JSON补充|
|GET /api/records/{id}/history|历次版本及原始记录|来源与变化追溯|
|PATCH /api/deadlines/{id}|done布尔值|仅修改学生本地完成标记|

导入完整字段由server/domain.py校验。稳定ID由记录类型、课程ID、来源URL、来源定位生成，与采集时间无关。所有导入先校验、后单事务保存，错误返回400且零写入。GET不调用CLI，不改变教学网。当前本地保存使用POST，与原计划后续“POST启动生成任务”分开。

课表记录为schedules数组，含title、weekday（1至7）、startTime/endTime（HH:mm，北京时间）、periods、location、rawText、note、source。只记录课程页明确给出的每周安排，不推算日期和教学周次；未识别到课表时不编造记录。版本和来源规则与其他记录一致。

## 后续CLI入口（协议已定，执行器未实现）

统一入口任务对象：taskType（replay/guidance/prep）、courseId、sourceRecordIds、contextVersionIds、outputPath、requestId。控制层固定材料快照，选择对应任务说明，将一次任务以非交互方式交给CLI。超时、退出失败或输出校验失败时保留上次成功结果。认证信息不得写入任务对象。

|任务|启动|读取|人工操作|原计划阶段|
|---|---|---|---|---|
|回放|POST /api/replay-jobs|GET /api/replay-jobs/{id}|核对摘要与时间点|阶段三|
|作业辅导|POST /api/guidance-jobs|GET /api/guidance-jobs/{id}|PATCH /api/drafts/{id}/review|阶段四|
|备考|POST /api/prep-jobs|GET /api/prep-jobs/{id}|PATCH /api/practice/{id}/answers|阶段五|

返回任务ID后轮询GET。通用状态queued/running/needs_materials/awaiting_review/failed/completed，失败包含可读原因，结果包含正文、sourceRecordIds、contextVersionIds与引用。生成过程不能写人工审核记录。

原甘特图的作业提交仍属于后续阶段，必须通过独立提交接口并取得用户当次具体授权。阶段二不执行、不声称实现。以上后续接口尚未注册到当前服务，不能在演示中假称可调用。
