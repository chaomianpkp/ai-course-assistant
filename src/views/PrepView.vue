<script setup>
import { computed, ref } from 'vue'
import { usePlatform } from '../composables/usePlatform'
import { mockQuestions, outline, pastQuestion } from '../data/catalog'

const { state, markOutlineReady, chooseMock, submitMock } = usePlatform()
const generating = ref(false)
const pastPick = ref(-1)
const pastShown = ref(false)

const answeredCount = computed(() => mockQuestions.filter((item) => state.mockAnswers[item.id] !== undefined).length)
const score = computed(
  () => mockQuestions.filter((item) => state.mockAnswers[item.id] === item.answer).length,
)

async function generate() {
  if (state.outlineReady || generating.value) return
  generating.value = true
  await new Promise((resolve) => setTimeout(resolve, 700))
  markOutlineReady()
  generating.value = false
}

function choosePast(index) {
  pastPick.value = index
  pastShown.value = true
}

function choiceClass(question, index) {
  if (!state.mockSubmitted) return state.mockAnswers[question.id] === index ? 'choice on' : 'choice'
  if (index === question.answer) return 'choice right'
  if (state.mockAnswers[question.id] === index) return 'choice wrong'
  return 'choice'
}
</script>

<template>
  <main class="page">
    <p class="kicker">备考 · 示例课程：软件工程</p>
    <h1>大纲、旧题和模拟卷都要能指回课堂材料</h1>
    <p class="lead">
      这一页用软件工程第 4、5 讲做示例。公开课和书只作对照，不把网络上的泛泛提纲直接当成复习范围。
    </p>

    <section>
      <div class="section-title">
        <h2>备考大纲</h2>
        <span>依据：第4讲、第5讲和课件</span>
      </div>
      <button v-if="!state.outlineReady" class="primary" type="button" :disabled="generating" @click="generate">
        {{ generating ? '正在对照课堂材料…' : '根据现有材料生成大纲' }}
      </button>
      <div v-else class="outline-grid">
        <article v-for="block in outline" :key="block.title" class="outline-card">
          <span class="badge pine">{{ block.source }}</span>
          <h3>{{ block.title }}</h3>
          <ul>
            <li v-for="item in block.items" :key="item">{{ item }}</li>
          </ul>
        </article>
      </div>
    </section>

    <section>
      <div class="section-title">
        <h2>往年题讲解</h2>
        <span>演示题，不是原卷</span>
      </div>
      <article class="detail">
        <h2 style="font-size: 22px">{{ pastQuestion.stem }}</h2>
        <button
          v-for="(option, index) in pastQuestion.options"
          :key="option"
          class="choice"
          :class="{
            right: pastShown && index === pastQuestion.answer,
            wrong: pastShown && pastPick === index && index !== pastQuestion.answer,
          }"
          type="button"
          @click="choosePast(index)"
        >
          {{ option }}
        </button>
        <p v-if="pastShown" class="explain">{{ pastQuestion.explain }}</p>
        <span v-if="pastShown" class="cites">
          <span v-for="cite in pastQuestion.cites" :key="cite" class="badge">{{ cite }}</span>
        </span>
      </article>
    </section>

    <section>
      <div class="section-title">
        <h2>模拟小卷</h2>
        <span v-if="state.mockSubmitted">{{ score }} / {{ mockQuestions.length }}</span>
        <span v-else>已答 {{ answeredCount }} / {{ mockQuestions.length }}</span>
      </div>
      <article v-for="question in mockQuestions" :key="question.id" class="detail" style="margin-bottom: 12px">
        <h2 style="font-size: 20px">{{ question.stem }}</h2>
        <button
          v-for="(option, index) in question.options"
          :key="option"
          :class="choiceClass(question, index)"
          type="button"
          :aria-pressed="state.mockAnswers[question.id] === index"
          @click="chooseMock(question.id, index)"
        >
          {{ option }}
        </button>
        <p v-if="state.mockSubmitted" class="explain">{{ question.explain }}</p>
      </article>
      <button class="primary" type="button" :disabled="answeredCount < mockQuestions.length || state.mockSubmitted" @click="submitMock">
        {{ state.mockSubmitted ? '已交卷' : '交卷并看解析' }}
      </button>
    </section>
  </main>
</template>
