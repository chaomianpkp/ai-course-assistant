import { computed, reactive, watch } from 'vue'
import {
  assignments,
  baseTasks,
  courses,
  deadlines,
  materials,
  replayTasks,
  replays,
} from '../data/catalog'

const STORAGE_KEY = 'keji-demo-v1'

function loadState() {
  try {
    return JSON.parse(localStorage.getItem(STORAGE_KEY)) || {}
  } catch {
    return {}
  }
}

const saved = loadState()

export const state = reactive({
  courseId: saved.courseId || 'all',
  doneTaskIds: saved.doneTaskIds || [],
  extraTasks: saved.extraTasks || [],
  addedReplays: saved.addedReplays || [],
  assignmentStatus: saved.assignmentStatus || {},
  outlineReady: Boolean(saved.outlineReady),
  mockAnswers: saved.mockAnswers || {},
  mockSubmitted: Boolean(saved.mockSubmitted),
})

watch(
  state,
  () => {
    localStorage.setItem(
      STORAGE_KEY,
      JSON.stringify({
        courseId: state.courseId,
        doneTaskIds: state.doneTaskIds,
        extraTasks: state.extraTasks,
        addedReplays: state.addedReplays,
        assignmentStatus: state.assignmentStatus,
        outlineReady: state.outlineReady,
        mockAnswers: state.mockAnswers,
        mockSubmitted: state.mockSubmitted,
      }),
    )
  },
  { deep: true },
)

export const tasks = computed(() => [...baseTasks, ...state.extraTasks])

export function matchesCourse(courseId) {
  return state.courseId === 'all' || state.courseId === courseId
}

export function toggleTask(id) {
  const index = state.doneTaskIds.indexOf(id)
  if (index >= 0) state.doneTaskIds.splice(index, 1)
  else state.doneTaskIds.push(id)
}

export function assignmentStatus(assignment) {
  return state.assignmentStatus[assignment.id] || (assignment.gap ? 'blocked' : 'draft')
}

export function setAssignmentStatus(id, status) {
  state.assignmentStatus[id] = status
}

export function addReplayTask(replayId) {
  if (state.addedReplays.includes(replayId)) return false
  const task = replayTasks[replayId]
  if (!task) return false
  state.addedReplays.push(replayId)
  state.extraTasks.push(task)
  return true
}

export function markOutlineReady() {
  state.outlineReady = true
}

export function chooseMock(id, index) {
  if (state.mockSubmitted) return
  state.mockAnswers[id] = index
}

export function submitMock() {
  state.mockSubmitted = true
}

export function resetDemo() {
  localStorage.removeItem(STORAGE_KEY)
  window.location.assign('/')
}

export function usePlatform() {
  return {
    state,
    courses,
    deadlines,
    materials,
    replays,
    assignments,
    tasks,
    matchesCourse,
    toggleTask,
    assignmentStatus,
    setAssignmentStatus,
    addReplayTask,
    markOutlineReady,
    chooseMock,
    submitMock,
    resetDemo,
  }
}
