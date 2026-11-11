<script setup>
import { computed, ref, watch } from 'vue'
import { usePlatform } from '../composables/usePlatform'
import { courseById } from '../data/catalog'
import { useRouter } from '../router'

const { state, materials, matchesCourse } = usePlatform()
const { query, push } = useRouter()
const keyword = ref('')
const selectedId = ref(query.value.id || '')

watch(
  () => query.value.id,
  (id) => {
    if (id) selectedId.value = id
  },
)

const visible = computed(() => {
  const text = keyword.value.trim()
  return materials.filter((item) => {
    if (!matchesCourse(item.courseId)) return false
    if (!text) return true
    return `${item.title}${item.note}${item.origin}${item.kind}`.includes(text)
  })
})

function toggle(id) {
  selectedId.value = selectedId.value === id ? '' : id
}
</script>

<template>
  <main class="page">
    <p class="kicker">资料收集</p>
    <h1>把课件、书单、公开课和群公告收在一门课下面</h1>
    <p class="lead">
      演示里这些材料已经整理好。之后可以换成从教学网、课程网站和群聊导入，并保留每份材料的来源。
    </p>

    <div class="filters">
      <input v-model="keyword" class="search" type="search" placeholder="搜索标题、来源或摘要" aria-label="搜索资料" />
    </div>

    <div class="stack">
      <article v-for="item in visible" :key="item.id" class="material">
        <button type="button" @click="toggle(item.id)">
          <header>
            <span class="badges">
              <span class="badge ink">{{ item.kind }}</span>
              <span class="badge pine">{{ item.status }}</span>
            </span>
            <span class="meta">{{ courseById(item.courseId).name }}</span>
          </header>
          <h3>{{ item.title }}</h3>
          <p class="meta">来源：{{ item.origin }}</p>
        </button>
        <div v-if="selectedId === item.id">
          <p>{{ item.note }}</p>
          <span class="cites">
            <button v-for="link in item.links" :key="link.href" class="cite" type="button" @click="push(link.href)">
              {{ link.label }}
            </button>
          </span>
        </div>
      </article>
      <p v-if="!visible.length" class="empty">没有符合条件的资料。可以清空搜索，或把顶部课程改回全部。</p>
    </div>
  </main>
</template>
