<script setup>
import { computed, ref, watch } from 'vue'
import { usePlatform } from '../composables/usePlatform'
import { courseById, dueLabel, formatDue } from '../data/catalog'
import { useRouter } from '../router'

const { assignments, matchesCourse, assignmentStatus, setAssignmentStatus } = usePlatform()
const { query, push } = useRouter()

const visible = computed(() => assignments.filter((item) => matchesCourse(item.courseId)))
const selectedId = ref(query.value.id || '')

const selected = computed(() => {
  const current = visible.value.find((item) => item.id === selectedId.value)
  return current || visible.value[0] || null
})

watch(visible, (list) => {
  if (!list.some((item) => item.id === selectedId.value)) selectedId.value = list[0]?.id || ''
})

const statusText = {
  draft: '草稿待确认',
  confirmed: '已确认，待自己改写',
  revise: '退回，仍用原文',
  blocked: '资料不足',
}

function statusClass(status) {
  if (status === 'confirmed') return 'pine'
  if (status === 'blocked') return 'alert'
  if (status === 'revise') return 'warn'
  return 'warn'
}

function openAssignment(id) {
  selectedId.value = id
  push(`/assignments?id=${id}`)
}
</script>

<template>
  <main class="page">
    <p class="kicker">作业辅导</p>
    <h1>作业从教学网、课程网站和微信群进来，草稿必须能指回来源</h1>
    <p class="lead">
      确认只表示这份结构可以接着改。操作系统实验因为缺少环境记录，会停住，不补写一份看起来完整的报告。
    </p>

    <div class="layout">
      <div class="stack">
        <button
          v-for="item in visible"
          :key="item.id"
          class="assignment"
          type="button"
          :aria-pressed="selected?.id === item.id"
          @click="openAssignment(item.id)"
        >
          <header>
            <span class="badge" :class="statusClass(assignmentStatus(item))">
              {{ statusText[assignmentStatus(item)] }}
            </span>
            <span class="badge">{{ item.sourceKind }}</span>
          </header>
          <h3>{{ item.title }}</h3>
          <p class="meta">{{ courseById(item.courseId).name }} · {{ dueLabel(item.due) }}</p>
        </button>
        <p v-if="!visible.length" class="empty">这门课还没有导入作业。</p>
      </div>

      <article v-if="selected" class="detail">
        <span class="badges">
          <span class="badge" :class="statusClass(assignmentStatus(selected))">
            {{ statusText[assignmentStatus(selected)] }}
          </span>
          <span class="badge">{{ dueLabel(selected.due) }} · {{ formatDue(selected.due) }}</span>
        </span>
        <h2>{{ selected.title }}</h2>
        <p class="meta">{{ courseById(selected.courseId).name }} · {{ selected.source }}</p>
        <p class="prompt">{{ selected.prompt }}</p>

        <p v-if="selected.gap" class="note block">{{ selected.gap }}</p>

        <template v-else>
          <div v-for="section in selected.draft" :key="section.heading" class="draft">
            <h3>{{ section.heading }}</h3>
            <p>{{ section.body }}</p>
            <span class="cites">
              <span v-for="cite in section.cites" :key="cite" class="badge">{{ cite }}</span>
            </span>
          </div>
          <p class="note">{{ selected.caution }}</p>
          <div class="actions">
            <button class="primary" type="button" @click="setAssignmentStatus(selected.id, 'confirmed')">
              确认这份草稿
            </button>
            <button class="ghost" type="button" @click="setAssignmentStatus(selected.id, 'revise')">
              先不采用
            </button>
            <button
              v-if="selected.id === 'se-srs'"
              class="ghost"
              type="button"
              @click="push('/replay?id=se-5')"
            >
              查看第5讲依据
            </button>
            <button
              v-if="selected.id === 'ds-hw3'"
              class="ghost"
              type="button"
              @click="push('/materials?id=ds-graph')"
            >
              打开图论课件
            </button>
          </div>
        </template>

        <div v-if="selected.gap" class="actions">
          <button class="primary" type="button" @click="push('/materials?id=os-lab-page')">查看已有实验材料</button>
          <button class="ghost" type="button" @click="push('/replay?id=os-6')">查看调度那一讲</button>
        </div>
      </article>
    </div>
  </main>
</template>
