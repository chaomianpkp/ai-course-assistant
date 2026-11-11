<script setup>
import { computed, ref } from 'vue'
import { useCourseStore } from '../composables/useCourseStore'
import { usePlatform } from '../composables/usePlatform'
import { useRouter } from '../router'

const { data, load, setDone } = useCourseStore()
const { state } = usePlatform()
const { push } = useRouter()
const error = ref('')
const saving = ref([])
const filter = ref('pending')
const courseName = (id) => data.courses.find((c) => c.id === id)?.name || id
const matches = (item) => state.courseId === 'all' || item.courseId === state.courseId
const schedules = computed(() => (data.schedules || []).filter(matches).sort((a,b)=>a.weekday-b.weekday || a.startTime.localeCompare(b.startTime)))
const weekday = n => '一二三四五六日'[n-1]
const materials = computed(() => data.materials.filter(matches))
const deadlines = computed(() => data.deadlines.filter(matches).filter((d) => filter.value === 'all' || (filter.value === 'done' ? d.done : !d.done)).sort((a, b) => new Date(a.due) - new Date(b.due)))
const unknownDeadlines = computed(() => data.materials.filter(matches).filter(d => d.category === '作业要求' && d.dueInfo && !d.dueInfo.due))
const pending = computed(() => data.deadlines.filter(matches).filter((d) => !d.done).length)
async function change(item, done) {
  saving.value.push(item.id)
  error.value = ''
  try { await setDone(item.id, done) }
  catch (e) { error.value = e.message }
  finally { saving.value = saving.value.filter((id) => id !== item.id) }
}
const format = (due) => new Date(due).toLocaleString('zh-CN', { timeZone: 'Asia/Shanghai', hour12: false })
</script>
<template>
  <main class="page">
    <p class="kicker">课程看板 · 第二阶段</p>
    <h1>资料与截止，回到同一门课</h1>
    <p class="lead">这里展示已保存的课程资料和你确认的截止时间。导入不包含个人提交记录，请核对后标记完成；标记仅用于个人跟进，不代表已向教学网提交。</p>
    <div class="stats"><article><strong>{{ data.courses.length }}</strong><span>已导入课程</span></article><article><strong>{{ materials.length }}</strong><span>当前课程资料</span></article><article><strong>{{ pending }}</strong><span>未标记完成</span></article></div>
    <div class="actions"><button class="primary" @click="push('/materials')">添加或查找资料</button><button class="ghost" :disabled="data.loading" @click="load">刷新课程数据</button></div>
    <p v-if="error" class="note block" role="alert">{{ error }}</p>
    <section aria-label="课程课表"><div class="section-title"><h2>课程课表</h2></div>
      <div class="stack"><article v-for="item in schedules" :key="item.id" class="material"><span class="badge">{{ courseName(item.courseId) }}</span><h3>周{{ weekday(item.weekday) }} {{ item.startTime }}–{{ item.endTime }}（北京时间）</h3><p>第 {{ item.periods || '待确认' }} 节 · {{ item.location }}</p><p class="meta">{{ item.note }}</p><a class="cite" :href="item.source.url" target="_blank" rel="noopener noreferrer">核对课表原页 ↗</a><details><summary>查看课表原文</summary><p>{{ item.rawText }}</p><p class="meta">{{ item.source.title }} · {{ item.source.locator }} · 版本 {{ item.version }}</p></details></article><p v-if="!schedules.length" class="empty">尚未导入可确认的课表。请从课程信息页采集，或导入带来源的课表清单；不以示例课表替代。</p></div>
    </section>
    <div class="section-title"><h2>截止清单</h2><select v-model="filter" aria-label="按完成状态筛选"><option value="pending">待完成</option><option value="done">已完成</option><option value="all">全部</option></select></div>
    <div class="stack">
      <article v-for="item in deadlines" :key="item.id" class="task" :class="{done: item.done}">
        <input type="checkbox" :checked="item.done" :disabled="saving.includes(item.id)" :aria-label="`标记完成：${item.title}`" @change="change(item, $event.target.checked)" />
        <div><span class="badge" :class="!item.done && new Date(item.due) < new Date() ? 'alert' : 'pine'">{{ item.done ? '已标记完成' : new Date(item.due) < new Date() ? '已过截止，待核实处理' : '未标记完成' }}</span><h3>{{ item.title }}</h3><p v-if="item.dueInfo?.note" class="note" :class="item.dueInfo.conflict ? 'block' : ''">{{ item.dueInfo.note }}</p><p>{{ courseName(item.courseId) }} · {{ format(item.due) }}（北京时间）</p><p class="meta">{{ item.source.title }} · {{ item.source.locator || '全文' }} · 版本 {{ item.version }}</p><a class="cite" :href="item.source.url" target="_blank" rel="noopener noreferrer">核对原始要求 ↗</a></div>
      </article>
      <p v-if="!deadlines.length" class="empty">{{ data.loading ? '正在读取…' : '当前没有符合条件的截止项。导入带截止时间的材料后，会显示在这里。' }}</p>
    </div>
    <section v-if="unknownDeadlines.length"><div class="section-title"><h2>截止待确认</h2></div><article v-for="item in unknownDeadlines" :key="item.id" class="material"><h3>{{ item.title }}</h3><p class="meta">{{ courseName(item.courseId) }} · 未识别到明确截止时间</p><a class="cite" :href="item.source.url" target="_blank" rel="noopener noreferrer">核对作业原页 ↗</a></article></section>
    <div class="section-title"><h2>最近保存的资料</h2><button class="ghost" @click="push('/materials')">查看全部资料</button></div>
    <div class="stack"><article v-for="item in materials.slice(0, 5)" :key="item.id" class="material"><span class="badge">{{ courseName(item.courseId) }}</span><h3>{{ item.title }}</h3><p class="meta">{{ item.source.title }} · {{ item.category }} · 版本 {{ item.version }}</p></article></div>
  </main>
</template>
