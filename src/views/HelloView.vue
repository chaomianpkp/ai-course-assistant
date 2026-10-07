<script setup>
import { useRouter } from '../router'

const { push } = useRouter()
</script>

<template>
  <main class="hello">
    <section class="hello-card">
      <p class="kicker">/test/hello</p>
      <h1>hello world</h1>
      <p class="lead">
        课迹是面向大学课程的 AI 辅助学习平台。这个地址保留给课程检查；旁边的五个页面是第一阶段可以演示的部分功能。
      </p>
      <div class="actions">
        <button class="primary" type="button" @click="push('/')">进入课程看板</button>
      </div>
    </section>
  </main>
</template>
