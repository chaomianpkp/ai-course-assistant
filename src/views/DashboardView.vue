<script setup>
import { computed } from 'vue'
import { usePlatform } from '../composables/usePlatform'
import { courseById, dueLabel, formatDue, todayHeadline, weekdays } from '../data/catalog'
import { useRouter } from '../router'

const { state, courses, deadlines, tasks, matchesCourse, toggleTask } = usePlatform()
const { push } = useRouter()
const today = new Date().getDay()

const visibleDeadlines = computed(() =>
  deadlines
    .filter((item) => matchesCourse(item.courseId))
    .slice()
    .sort((a, b) => new Date(a.due) - new Date(b.due)),
)

const visibleTasks = computed(() => tasks.value.filter((item) => matchesCourse(item.courseId)))

function sessionsOn(weekday) {
  return courses.filter((course) => course.weekday === weekday)
}
</script>

<template>
  <main class="page">
    <p class="kicker">课程看板</p>
    <h1>{{ todayHeadline() }}</h1>
    <p class="lead">
      把教室、上课时间和作业截止放在一处。任务来自课件、回放和作业要求，做完可以在这里勾掉。
    </p>

    <section class="week" aria-label="本周课表">
      <article v-for="day in weekdays" :key="day.id" class="day" :class="{ today: day.id === today }">
        <header>
          <span>{{ day.label }}</span>
          <span>{{ day.id === today ? '今天' : '' }}</span>
        </header>
        <div v-for="course in sessionsOn(day.id)" :key="course.id" class="session">
          <strong><i class="dot" :style="{ '--accent': course.accent }"></i>{{ course.name }}</strong>
          <p>{{ course.slot }} · {{ course.time }}</p>
          <p>{{ course.room }}</p>
        </div>
        <p v-if="!sessionsOn(day.id).length" class="meta" style="margin-top: 18px">无课</p>
      </article>
    </section>

    <div class="split">
      <section>
        <div class="section-title">
          <h2>近期截止</h2>
          <span>{{ visibleDeadlines.length }} 项</span>
        </div>
        <div class="stack">
          <button
            v-for="item in visibleDeadlines"
            :key="item.id"
            class="deadline"
            type="button"
            @click="push(`/assignments?id=${item.id}`)"
          >
            <header>
              <span class="badge" :class="dueLabel(item.due) === '明天截止' ? 'alert' : 'warn'">
                {{ dueLabel(item.due) }}
              </span>
              <span class="badge">{{ item.sourceKind }}</span>
            </header>
            <h3>{{ item.title }}</h3>
            <p>{{ courseById(item.courseId).name }} · {{ formatDue(item.due) }}</p>
            <p class="meta">来源：{{ item.source }}</p>
          </button>
          <p v-if="!visibleDeadlines.length" class="empty">这门课暂时没有截止项。</p>
        </div>
      </section>

      <section>
        <div class="section-title">
          <h2>可执行任务</h2>
          <span>勾选后保存在本机</span>
        </div>
        <div class="stack">
          <div v-for="task in visibleTasks" :key="task.id" class="task" :class="{ done: state.doneTaskIds.includes(task.id) }">
            <input
              type="checkbox"
              :checked="state.doneTaskIds.includes(task.id)"
              :aria-label="task.title"
              @change="toggleTask(task.id)"
            />
            <span>
              <h3>{{ task.title }}</h3>
              <p class="meta">{{ courseById(task.courseId).name }}</p>
              <span class="cites">
                <button
                  v-for="source in task.sources"
                  :key="source.href"
                  class="cite"
                  type="button"
                  @click="push(source.href)"
                >
                  {{ source.label }}
                </button>
              </span>
            </span>
          </div>
          <p v-if="!visibleTasks.length" class="empty">这门课还没有生成任务。可以先去回放页整理一讲。</p>
        </div>
      </section>
    </div>

    <div class="section-title">
      <h2>课程信息</h2>
      <span>点一门课，只看它的资料和作业</span>
    </div>
    <div class="courses">
      <button
        v-for="course in courses"
        :key="course.id"
        class="course-card"
        :class="{ selected: state.courseId === course.id }"
        type="button"
        :style="{ '--accent': course.accent }"
        @click="state.courseId = course.id"
      >
        <span class="badge">{{ course.slot }}</span>
        <h3>{{ course.name }}</h3>
        <p>{{ course.time }}</p>
        <p>{{ course.room }}</p>
      </button>
    </div>
  </main>
</template>
