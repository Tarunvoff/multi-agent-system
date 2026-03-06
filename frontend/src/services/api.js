import axios from 'axios'

const api = axios.create({
  baseURL: '',          // relative — routed through Vite proxy → http://localhost:8001
  headers: { 'Content-Type': 'application/json' },
  timeout: 600000,      // 10 min — local LLM inference is slow
})

/**
 * Submit a new task query with an optional custom pipeline.
 *
 * @param {string}   query       - The research question.
 * @param {string[]} [agentNames] - Ordered list of agent names, e.g.
 *                                  ['planner','researcher','factchecker','writer'].
 *                                  Omit to use the server-side default pipeline.
 */
export async function submitTask(query, agentNames = null) {
  const body = { query }
  if (agentNames && agentNames.length > 0) {
    body.pipeline = { agents: agentNames }
  }
  const { data } = await api.post('/run', body)
  return data
}

/**
 * Fetch all tasks, newest first.
 * GET /tasks
 */
export async function fetchTasks() {
  const { data } = await api.get('/tasks')
  return data
}

/**
 * Fetch a single task by ID.
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
