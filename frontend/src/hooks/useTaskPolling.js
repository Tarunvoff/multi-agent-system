import { useState, useEffect, useRef } from 'react'
import { fetchTask } from '../services/api'

/**
 * Polls GET /task/{taskId} every 2 seconds.
 * Stops automatically when status === 'completed'.
 */
export function useTaskPolling(taskId) {
  const [task, setTask] = useState(null)
  const [error, setError] = useState(null)
  const intervalRef = useRef(null)

  useEffect(() => {
    if (!taskId) return

    const poll = async () => {
      try {
        const data = await fetchTask(taskId)
        setTask(data)
        if (data.status === 'completed') {
          clearInterval(intervalRef.current)
        }
      } catch (err) {
        setError(err.message || 'Polling error')
        clearInterval(intervalRef.current)
      }
    }

    poll()
    intervalRef.current = setInterval(poll, 1500)

    return () => clearInterval(intervalRef.current)
  }, [taskId])

  return { task, error }
}
