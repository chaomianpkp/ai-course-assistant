<script setup>
import { computed, ref, watch } from 'vue'
import { usePlatform } from '../composables/usePlatform'
import { courseById } from '../data/catalog'
import { useRouter } from '../router'

const { state, replays, matchesCourse, addReplayTask } = usePlatform()
const { query, push } = useRouter()

const visible = computed(() => replays.filter((item) => matchesCourse(item.courseId)))
const selectedId = ref(query.value.id || visible.value[0]?.id || '')
const activeTime = ref('')
const addedNote = ref('')

const selected = computed(
  () => visible.value.find((item) => item.id === selectedId.value) || visible.value[0] || null,
)

watch(
  selected,
  (replay) => {
    activeTime.value = replay?.points[0]?.time || ''
    addedNote.value = ''
  },
  { immediate: true },
)

watch(visible, (list) => {
  if (!list.some((item) => item.id === selectedId.value)) {
    selectedId.value = list[0]?.id || ''
  }
})

function selectReplay(id) {
  selectedId.value = id
  push(`/replay?id=${id}`)
}

function focusPoint(time) {
  activeTime.value = time
}

function collect() {
  if (!selected.value) return
  const created = addReplayTask(selected.value.id)
  addedNote.value = created ? '已放到课程看板的任务里。' : '这讲的任务已经在看板里。'
}
</script>

<template>
  <main class="page">
    <p class="kicker">回放整理</p>
    <h1>回放先转成文字，再收成可以回到时间点的知识点</h1>
    <p class="lead">演示使用已经整理好的三讲。正式版本再接入教学网下载和转写，这一页的结构可以保留。</p>

    <div class="layout">
      <div class="stack">
        <button
          v-for="item in visible"
          :key="item.id"
          class="lecture"
          type="button"
          :aria-pressed="selected?.id === item.id"
          @click="selectReplay(item.id)"
        >
          <header>
            <span class="badge" :class="item.status === '已整理' ? 'pine' : 'warn'">{{ item.status }}</span>
            <span class="meta">{{ item.date }}</span>
          </header>
          <h3>{{ item.title }}</h3>
          <p class="meta">{{ courseById(item.courseId).name }} · {{ item.duration }}</p>
        </button>
        <p v-if="!visible.length" class="empty">这门课还没有回放。</p>
      </div>

      <article v-if="selected" class="detail">
        <span class="badge">{{ courseById(selected.courseId).name }}</span>
        <h2>{{ selected.title }}</h2>
        <p class="meta">{{ selected.date }} · {{ selected.duration }} · {{ selected.status }}</p>
        <ul class="summary">
          <li v-for="line in selected.summary" :key="line">{{ line }}</li>
        </ul>

        <div class="actions">
          <button class="primary" type="button" :disabled="state.addedReplays.includes(selected.id)" @click="collect">
            {{ state.addedReplays.includes(selected.id) ? '已生成学习任务' : '整理成学习任务' }}
          </button>
          <button class="ghost" type="button" @click="push('/')">回到看板</button>
        </div>
        <p v-if="addedNote" class="note ok">{{ addedNote }}</p>

        <div class="timeline" aria-label="知识点时间">
          <button
            v-for="point in selected.points"
            :key="point.time"
            type="button"
            :aria-pressed="activeTime === point.time"
            @click="focusPoint(point.time)"
          >
            {{ point.time }} {{ point.title }}
          </button>
        </div>

        <div
          v-for="point in selected.points"
          :key="point.title"
          class="point"
          :class="{ active: activeTime === point.time }"
        >
          <header>
            <strong>{{ point.time }}</strong>
            <span class="meta">{{ point.source }}</span>
          </header>
          <h3>{{ point.title }}</h3>
          <p>{{ point.detail }}</p>
        </div>

        <div class="section-title">
          <h2>转写片段</h2>
        </div>
        <div class="transcript">
          <p v-for="line in selected.transcript" :key="line.time" class="line" :class="{ active: activeTime === line.time }">
            <time>{{ line.time }}</time>
            <span>{{ line.text }}</span>
          </p>
        </div>

      </article>
    </div>
  </main>
</template>
