import axios from 'axios'

const api = axios.create({
  baseURL: '',          // relative — routed through Vite proxy → http://localhost:8001
  headers: { 'Content-Type': 'application/json' },
  timeout: 600000,      // 10 min — local LLM inference is slow
})

/**
 * Submit a new task query.
 * POST /run  { query }
 * Returns the initial Task object immediately (status: "planning").
 * The pipeline runs in the background — poll GET /task/{id} for live updates.
 */
export async function submitTask(query) {
  const { data } = await api.post('/run', { query })
  return data
}

/**
 * Fetch a task by ID.
 * GET /task/{taskId}
 */
export async function fetchTask(taskId) {
  const { data } = await api.get(`/task/${taskId}`)
  return data
}

/**
 * Fetch the timeline for a task.
 * GET /task/{taskId}/timeline
 */
export async function fetchTimeline(taskId) {
  const { data } = await api.get(`/task/${taskId}/timeline`)
  return data
}

/**
 * Fetch the pipeline breakdown for a task.
 * GET /task/{taskId}/pipeline
 */
export async function fetchPipeline(taskId) {
  const { data } = await api.get(`/task/${taskId}/pipeline`)
  return data
}
