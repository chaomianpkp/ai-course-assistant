import { reactive } from 'vue'

const data = reactive({ courses: [], materials: [], deadlines: [], schedules: [], collections: [], loading: false, loaded: false, error: '' })

async function request(path, options = {}) {
  let response
  try {
    response = await fetch(path, { ...options, headers: { 'Content-Type': 'application/json', ...options.headers } })
  } catch {
    throw new Error('无法连接本地课程服务，请检查服务是否正在运行。')
  }
  const body = await response.json().catch(() => ({ error: '服务没有返回有效数据，请检查本地课程服务。' }))
  if (!response.ok) throw new Error(body.error || '请求失败，请重试。')
  return body
}

async function load() {
  data.loading = true
  data.error = ''
  try {
    const catalog = await request('/api/catalog')
    Object.assign(data, catalog, { loaded: true })
  } catch (error) {
    data.error = error.message
  } finally {
    data.loading = false
  }
}

async function importBundle(bundle) {
  const result = await request('/api/imports', { method: 'POST', body: JSON.stringify(bundle) })
  await load()
  if (data.error) throw new Error(`已保存，但刷新列表失败：${data.error}`)
  return result
}

async function setDone(id, done) {
  const result = await request(`/api/deadlines/${id}`, { method: 'PATCH', body: JSON.stringify({ done }) })
  const record = data.deadlines.find((item) => item.id === id)
  if (record) record.done = result.done
}

export function useCourseStore() {
  return { data, load, importBundle, setDone, connector: () => request('/api/connector'), history: (id) => request(`/api/records/${id}/history`) }
}
