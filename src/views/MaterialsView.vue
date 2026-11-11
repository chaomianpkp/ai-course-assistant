<script setup>
import { computed, ref } from 'vue'
import { useCourseStore } from '../composables/useCourseStore'
import { usePlatform } from '../composables/usePlatform'

const { data, importBundle, history, connector, load } = useCourseStore()
const { state } = usePlatform()
const pairingCode = ref('')
async function copyConnection() {
  try { pairingCode.value = (await connector()).pairingCode; await navigator.clipboard.writeText(pairingCode.value); message.value = '连接码已复制，请粘贴到教学网导入助手。'; }
  catch(e) { error.value = e.message }
}
const syncs = computed(() => data.collections.filter(item => state.courseId === 'all' || item.courseId === state.courseId))
const keyword = ref('')
const category = ref('all')
const jsonText = ref('')
const busy = ref(false)
const message = ref('')
const error = ref('')
const expanded = ref('')
const versions = ref([])
const form = ref({ courseId: '', courseName: '', title: '', category: '课件摘录', sourceTitle: '', url: '', locator: '', content: '', due: '' })
const matches = (item) => state.courseId === 'all' || item.courseId === state.courseId
const visible = computed(() => data.materials.filter((item) => matches(item) &&
  (category.value === 'all' || item.category === category.value) &&
  `${item.title} ${item.content} ${item.source.title} ${item.source.locator}`.toLocaleLowerCase().includes(keyword.value.trim().toLocaleLowerCase())))
const categories = computed(() => [...new Set(data.materials.map((item) => item.category))])
const courseName = (id) => data.courses.find((c) => c.id === id)?.name || id

async function submit(bundle) {
  busy.value = true
  message.value = error.value = ''
  try {
    const result = await importBundle(bundle)
    state.courseId = bundle.course.id
    message.value = `导入完成：新增 ${result.inserted} 条，更新 ${result.updated} 条，未变化 ${result.unchanged} 条。`
  } catch (e) { error.value = e.message }
  finally { busy.value = false }
}
function submitForm() {
  const f = form.value
  const source = { title: f.sourceTitle, url: f.url, locator: f.locator }
  const bundle = { course: { id: f.courseId, name: f.courseName }, materials: [{ title: f.title, category: f.category, content: f.content, source }] }
  if (f.due) bundle.deadlines = [{ title: f.title, due: f.due + ':00+08:00', source }]
  return submit(bundle)
}
async function submitJson() {
  try { await submit(JSON.parse(jsonText.value)) }
  catch { error.value = 'JSON格式无效，请检查括号、引号和逗号。' }
}
async function readFile(event) {
  error.value = ''
  const file = event.target.files?.[0]
  if (!file) return
  if (file.size > 2 * 1024 * 1024) { error.value = '文件超过2MB。'; return }
  try { jsonText.value = await file.text() }
  catch { error.value = '文件读取失败，请重新选择。' }
}
async function showHistory(id) {
  expanded.value = id
  versions.value = []
  try { versions.value = (await history(id)).versions }
  catch (e) { error.value = e.message }
}
</script>

<template>
  <main class="page">
    <p class="kicker">资料收集 · 第二阶段</p>
    <h1>把课程材料和出处一起收好</h1>
    <p class="lead">从已登录的教学网课程采集通知、作业与课件目录，预览后保存到课迹。也可以手动补充材料。</p>
    <p v-if="message" class="note ok" role="status">{{ message }}</p>
    <p v-if="error" class="note block" role="alert">{{ error }}</p>
    <section class="detail import-box" aria-label="教学网导入">
      <h2>从北大教学网导入</h2>
      <p>打开已登录的课程页面，使用“课迹教学网导入助手”采集并核对，再输入连接码保存。课件仅导入目录与链接。</p>
      <div class="actions"><a class="ghost" href="https://course.pku.edu.cn/" target="_blank" rel="noopener noreferrer">打开教学网 ↗</a><button class="primary" @click="copyConnection">复制导入连接码</button><button class="ghost" :disabled="data.loading" @click="load">刷新导入结果</button></div>
      <details><summary>首次安装导入助手</summary><p>在Chrome扩展管理页开启开发者模式，选择“加载已解压的扩展程序”，选项目中的 browser-extension 文件夹。只需安装一次；每次采集均由你点击触发。</p><p>连接码只用于本机课迹，重启服务后失效。助手不读取Cookie、成绩或已提交作业正文。</p></details>
      <article v-for="sync in syncs" :key="sync.courseId" class="sync-summary">
        <strong>{{ courseName(sync.courseId) }}</strong><p class="meta">最近核查：{{ new Date(sync.checkedAt).toLocaleString('zh-CN') }}</p>
        <span class="badge">通知 {{ sync.sections.notices.count }} 条</span> <span class="badge">作业 {{ sync.sections.assignments.count }} 项</span> <span class="badge">课件目录 {{ sync.sections.courseware.count }} 项</span>
        <span v-if="sync.timetable" class="badge">课表 {{ sync.timetable.count }} 项{{ sync.timetable.status === 'unrecognized' ? '（待补充）' : '' }}</span>
        <p class="meta" v-if="sync.sections.notices.count === 0">本次成功检查通知栏，未见通知。</p>
      </article>
      <p v-if="!syncs.length" class="meta">尚无本课程的教学网采集记录。</p>
    </section>
    <details class="detail import-box">
      <summary>添加课程材料</summary>
      <form @submit.prevent="submitForm" class="import-form">
        <label>课程代号<input v-model="form.courseId" required pattern="[A-Za-z0-9_-]+" placeholder="例如 pku-se" maxlength="80" /></label>
        <label>课程名称<input v-model="form.courseName" required placeholder="例如 软件工程" maxlength="200" /></label>
        <label>资料标题<input v-model="form.title" required maxlength="500" /></label>
        <label>资料类型<select v-model="form.category"><option>课件摘录</option><option>作业要求</option><option>课程说明</option><option>阅读资料</option></select></label>
        <label>来源标题<input v-model="form.sourceTitle" required placeholder="原页面或文件的名称" maxlength="500" /></label>
        <label>来源链接<input v-model="form.url" required type="url" placeholder="https://…" maxlength="2000" /></label>
        <label>来源定位<input v-model="form.locator" placeholder="页码、章节或作业编号；同一来源多项内容请区分" maxlength="500" /></label>
        <label>截止时间（可选，北京时间）<input v-model="form.due" type="datetime-local" /></label>
        <label class="span-all">材料正文<textarea v-model="form.content" required rows="5" maxlength="100000" placeholder="粘贴已经取得的文字；PDF请先选取所需段落。" /></label>
        <div class="span-all actions"><button class="primary" :disabled="busy || !data.loaded">{{ busy ? '正在保存…' : '保存资料' }}</button></div>
      </form>
    </details>
    <details class="detail import-box">
      <summary>批量导入资料清单</summary>
      <p class="meta">选择 JSON 后先检查内容，再点击导入。同一来源与定位再次导入会更新版本，不重复新增。</p>
      <label class="file-label">选择资料清单<input type="file" accept=".json,application/json" @change="readFile" /></label>
      <textarea v-model="jsonText" rows="8" aria-label="资料清单JSON" placeholder='{"course":{"id":"pku-se","name":"软件工程"},"materials":[…]}' />
      <button class="primary" :disabled="busy || !data.loaded || !jsonText.trim()" @click="submitJson">确认导入清单</button>
    </details>
    <div class="section-title"><h2>课程资料</h2><span>{{ visible.length }} 条</span></div>
    <div class="filters">
      <input v-model="keyword" class="search" type="search" aria-label="搜索资料" placeholder="搜索标题、正文或来源" />
      <select v-model="category" aria-label="按资料类型筛选"><option value="all">全部类型</option><option v-for="kind in categories" :key="kind">{{ kind }}</option></select>
    </div>
    <div class="stack">
      <article v-for="item in visible" :key="item.id" class="material">
        <header><span class="badge pine">{{ courseName(item.courseId) }}</span><span class="meta">{{ item.category }} · 版本 {{ item.version }}</span></header>
        <h3>{{ item.title }}</h3><p class="meta">来源：{{ item.source.title }} · {{ item.source.locator || '全文' }}</p>
        <p v-if="item.dueInfo?.note" class="note" :class="item.dueInfo.conflict ? 'block' : ''">{{ item.dueInfo.note }}</p>
        <p class="source-content">{{ item.content }}</p>
        <ul v-if="item.attachments?.length" class="attachment-list"><li v-for="file in item.attachments" :key="file.url"><a :href="file.url" target="_blank" rel="noopener noreferrer">{{ file.title }} ↗</a></li></ul>
        <details v-if="item.dueInfo?.evidence?.length"><summary>查看截止依据</summary><p v-for="(v,index) in item.dueInfo.evidence" :key="index" class="meta">{{ v.source }}：{{ v.text }} {{ v.inferredYear ? '（年份按采集日期推定）' : '' }}</p></details>
        <div class="actions"><a class="cite" :href="item.source.url" target="_blank" rel="noopener noreferrer">打开原始来源 ↗</a><button class="ghost" @click="showHistory(item.id)">查看历史版本</button></div>
        <div v-if="expanded === item.id" class="version-list">
          <details v-for="v in versions" :key="v.version"><summary>版本 {{ v.version }} · {{ new Date(v.recordedAt).toLocaleString('zh-CN') }}</summary><p class="source-content">{{ v.record.content }}</p></details>
        </div>
      </article>
      <p v-if="!visible.length" class="empty">{{ data.loading ? '正在读取资料…' : '暂无符合条件的资料。先添加材料，或调整课程和搜索条件。' }}</p>
    </div>
  </main>
</template>
