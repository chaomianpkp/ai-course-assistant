// 课程看板上的初始学习任务。回放页追加的任务在 replays.js。
export const baseTasks = [
  {
    id: 't-se-outline',
    courseId: 'se',
    title: '按第 5 讲的四段结构，列出需求规格说明书目录',
    sources: [
      { label: '第5讲 18:40', href: '/replay?id=se-5' },
      { label: '课件第 12 页', href: '/materials?id=se-slides-5' },
    ],
  },
  {
    id: 't-ds-trace',
    courseId: 'ds',
    title: '对照课件例图，自己写出 BFS 和 DFS 的过程，先不要看最终序列',
    sources: [
      { label: '群公告', href: '/assignments?id=ds-hw3' },
      { label: '图论课件', href: '/materials?id=ds-graph' },
    ],
  },
  {
    id: 't-os-env',
    courseId: 'os',
    title: '补上实验环境记录后，再开始写调度实验报告',
    sources: [{ label: '实验二', href: '/assignments?id=os-lab2' }],
  },
]
