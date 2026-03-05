import React, { useState, useEffect } from 'react'
import { submitTask } from '../services/api'

export default function TaskInput({ onTaskStarted, initialQuery = '' }) {
  const [query, setQuery]     = useState(initialQuery)
  const [loading, setLoading] = useState(false)
  const [error, setError]     = useState(null)

  // Sync when a suggested query is picked from the hero
  useEffect(() => {
    if (initialQuery) setQuery(initialQuery)
  }, [initialQuery])

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!query.trim()) return
    setLoading(true)
    setError(null)
    try {
      const task = await submitTask(query.trim())
      onTaskStarted(task)
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Failed to start task')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div>
      <form onSubmit={handleSubmit} className="flex gap-2">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Ask anything — e.g. Explain quantum entanglement"
          disabled={loading}
          autoFocus
          className="flex-1 px-5 py-3.5 text-sm rounded-2xl border border-white/10 bg-white/6
                     placeholder-white/30 text-white focus:outline-none focus:ring-2
                     focus:ring-indigo-400/50 focus:bg-white/10 transition-all disabled:opacity-50"
        />
        <button
          type="submit"
          disabled={loading || !query.trim()}
          className="px-6 py-3.5 bg-indigo-500 hover:bg-indigo-400 active:bg-indigo-600
                     disabled:opacity-40 text-white text-sm font-semibold rounded-2xl
                     transition-all shadow-lg shadow-indigo-950/60 flex items-center gap-2 whitespace-nowrap"
        >
          {loading ? (
            <>
              <svg className="w-4 h-4 animate-spin" viewBox="0 0 24 24" fill="none">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z" />
              </svg>
              Starting…
            </>
          ) : (
            <>
              Run Pipeline
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
              </svg>
            </>
          )}
        </button>
      </form>

      {error && (
        <p className="mt-3 text-xs text-red-400 bg-red-400/10 border border-red-400/20 rounded-xl px-4 py-2.5">
          ⚠ {error}
        </p>
      )}
    </div>
  )
}
