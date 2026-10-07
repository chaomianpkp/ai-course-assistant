import { computed, ref } from 'vue'

function readLocation() {
  const url = new URL(window.location.href)
  let path = url.pathname
  if (path.length > 1 && path.endsWith('/')) path = path.slice(0, -1)
  return {
    path,
    query: Object.fromEntries(url.searchParams.entries()),
  }
}

const current = ref(readLocation())

window.addEventListener('popstate', () => {
  current.value = readLocation()
})

export function useRouter() {
  function push(to) {
    const url = new URL(to, window.location.origin)
    const next = url.pathname + url.search
    if (next !== window.location.pathname + window.location.search) {
      window.history.pushState({}, '', next)
    }
    current.value = readLocation()
  }

  return {
    path: computed(() => current.value.path),
    query: computed(() => current.value.query),
    push,
  }
}
