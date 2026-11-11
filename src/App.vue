<script setup>
import { computed, watch, onMounted } from 'vue'
import AssignmentsView from './views/AssignmentsView.vue'
import DashboardView from './views/DashboardView.vue'
import HelloView from './views/HelloView.vue'
import MaterialsView from './views/MaterialsView.vue'
import PrepView from './views/PrepView.vue'
import ReplayView from './views/ReplayView.vue'
import DashboardDemoView from './views/DashboardDemoView.vue'
import MaterialsDemoView from './views/MaterialsDemoView.vue'
import { useCourseStore } from './composables/useCourseStore'
import { usePlatform } from './composables/usePlatform'
import { formatToday } from './data/catalog'
import { useRouter } from './router'

const nav = [
  { to: '/', label: '课程看板', hint: '时间、教室、截止' },
  { to: '/materials', label: '资料收集', hint: '课件、书和相关课' },
  { to: '/replay', label: '回放整理（原型）', hint: '转写、摘要、知识点' },
  { to: '/assignments', label: '作业辅导（原型）', hint: '来源和可确认草稿' },
  { to: '/prep', label: '备考（原型）', hint: '大纲、旧题、模拟' },
]

const views = {
  '/': DashboardView,
  '/materials': MaterialsView,
  '/replay': ReplayView,
  '/assignments': AssignmentsView,
  '/prep': PrepView,
  '/test/hello': HelloView,
  '/demo/dashboard': DashboardDemoView,
  '/demo/materials': MaterialsDemoView,
}

const titles = {
  '/': '课程看板',
  '/materials': '资料收集',
  '/replay': '回放整理',
  '/assignments': '作业辅导',
  '/prep': '备考',
  '/test/hello': 'hello world',
}

const { path, push } = useRouter()
const { state, courses: demoCourses, resetDemo } = usePlatform()
const { data, load } = useCourseStore()
const isLive = computed(() => ['/', '/materials'].includes(path.value))
const courses = computed(() => isLive.value ? data.courses : demoCourses)
onMounted(load)
watch([path, () => data.courses.length], () => {
  if (state.courseId !== 'all' && !courses.value.some((c) => c.id === state.courseId)) state.courseId = 'all'
})
const view = computed(() => views[path.value] || null)
const todayLabel = formatToday()

watch(
  path,
  (value) => {
    document.title = `${titles[value] || '课迹'} · 课迹`
  },
  { immediate: true },
)

function open(to) {
  push(to)
}
</script>

<template>
  <div class="shell">
    <aside class="rail">
      <div class="brand">
        <span class="logo">迹</span>
        <div>
          <strong>课迹</strong>
          <em>可追溯的课程辅导</em>
        </div>
      </div>
      <nav class="nav" aria-label="功能">
        <button
          v-for="item in nav"
          :key="item.to"
          type="button"
          :aria-current="path === item.to ? 'page' : undefined"
          @click="open(item.to)"
        >
          {{ item.label }}
          <small>{{ item.hint }}</small>
        </button>
      </nav>
      <div class="rail-foot">
        <p>看板与资料由本地服务保存。回放、作业辅导与备考为第一阶段原型。</p>
        <button type="button" @click="resetDemo">重置原型状态</button>
        <button class="hello-link" type="button" @click="open('/test/hello')">/test/hello</button>
      </div>
    </aside>

    <div class="stage">
      <header class="topbar">
        <p>2026 秋季学期 · {{ todayLabel }}</p>
        <label class="course-select">
          查看课程
          <select v-model="state.courseId" aria-label="按课程筛选">
            <option value="all">全部课程</option>
            <option v-for="course in courses" :key="course.id" :value="course.id">
              {{ course.name }}
            </option>
          </select>
        </label>
      </header>
      <div v-if="isLive && data.error" class="page"><p class="note block" role="alert">{{ data.error }}</p><button class="ghost" @click="load">重新连接</button></div>
      <component :is="view" v-if="view" />
      <main v-else class="page">
        <p class="kicker">课迹</p>
        <h1>没有这个页面</h1>
        <p class="lead">地址没有对应的功能。可以回到课程看板，或打开 /test/hello。</p>
        <div class="actions">
          <button class="primary" type="button" @click="open('/')">回到看板</button>
          <button class="ghost" type="button" @click="open('/test/hello')">打开 hello world</button>
        </div>
      </main>
    </div>
  </div>
</template>
