# 课迹

面向大学课程的 AI 辅助学习演示。把课表、资料、回放、作业和备考放在一起，并让每条辅导都能回到课堂来源。

当前是可点击原型：内容写在本地，不连接教学网。浏览器里的勾选和确认保存在 `localStorage`。

## 目录

| 路径 | 内容 |
| --- | --- |
| `src/views/DashboardView.vue` | 课程看板 |
| `src/views/MaterialsView.vue` | 资料收集 |
| `src/views/ReplayView.vue` | 回放整理 |
| `src/views/AssignmentsView.vue` | 作业辅导 |
| `src/views/PrepView.vue` | 备考 |
| `src/views/HelloView.vue` | `/test/hello` |
| `src/data/` | 各模块的演示数据，入口是 `catalog.js` |
| `src/composables/usePlatform.js` | 筛选、勾选、确认、模拟卷等本机状态 |
| `src/router.js` | 路径切换 |
| `src/App.vue` | 侧栏和顶栏 |
| `src/style.css` | 界面样式 |

改某一门功能时，优先只动对应的 `views` 文件和 `data` 文件。

## 本地运行

```bash
npm install
npm run dev
```

打开 http://127.0.0.1:5173/ 。侧栏「重置演示」恢复初始数据。

## 演示顺序

1. 课程看板：看今天的课、教室，以及来自微信群、课程网站、教学网的三个截止。勾掉一条学习任务。
2. 回放整理：打开「第5讲 用例与需求规格」，点时间点对照转写，再点「整理成学习任务」。
3. 回到看板，确认新任务出现。
4. 作业辅导：打开需求规格说明书，看草稿上的来源，点「确认这份草稿」。再打开操作系统实验，确认资料不足时不会生成报告。
5. 备考：生成大纲，选一道往年题看解析，做完三题模拟后交卷。
6. 打开 `/test/hello`，页面上有 `hello world`。

右上角可以按课程筛选。演示数据里，数据结构作业只提示写法，不给出最终遍历序列。

## 和参考项目的差别

[AutoPku](https://github.com/WindGraham/AutoPku) 在本机用 Agent 拉取教学网通知并处理作业。课迹是网页，学生先看到来源和待确认任务，再决定是否采用草稿。
