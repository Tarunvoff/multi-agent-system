import React, { useState, useEffect } from 'react'
import { submitTask } from '../services/api'

const ALL_AGENTS = ['planner', 'researcher', 'factchecker', 'writer', 'reviewer']
const DEFAULT_AGENTS = ['planner', 'researcher', 'writer', 'reviewer']

export default function TaskInput({ onTaskStarted, initialQuery = '' }) {
  const [query, setQuery]               = useState(initialQuery)
  const [loading, setLoading]           = useState(false)
  const [error, setError]               = useState(null)
  const [showPipeline, setShowPipeline] = useState(false)
  const [selectedAgents, setSelectedAgents] = useState(DEFAULT_AGENTS)

  // Sync when a suggested query is picked from the hero
  useEffect(() => {
    if (initialQuery) setQuery(initialQuery)
  }, [initialQuery])

  const toggleAgent = (agent) => {
    setSelectedAgents(prev =>
      prev.includes(agent) ? prev.filter(a => a !== agent) : [...prev, agent]
    )
  }

  // Preserve canonical ordering
  const orderedSelection = ALL_AGENTS.filter(a => selectedAgents.includes(a))

  const isDefaultPipeline =
    orderedSelection.length === DEFAULT_AGENTS.length &&
    orderedSelection.every((a, i) => a === DEFAULT_AGENTS[i])

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!query.trim() || orderedSelection.length === 0) return
    setLoading(true)
    setError(null)
    try {
      const pipeline = isDefaultPipeline ? null : orderedSelection
      const task = await submitTask(query.trim(), pipeline)
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
          disabled={loading || !query.trim() || orderedSelection.length === 0}
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

      {/* Pipeline configurator */}
      <div className="mt-3">
        <button
          type="button"
          onClick={() => setShowPipeline(v => !v)}
          className="text-xs text-white/35 hover:text-white/60 transition-colors flex items-center gap-1"
        >
          <svg className={`w-3 h-3 transition-transform ${showPipeline ? 'rotate-90' : ''}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
          </svg>
          ? Configure pipeline
          {!isDefaultPipeline && (
            <span className="ml-1.5 px-1.5 py-0.5 rounded-full bg-indigo-500/20 text-indigo-300 text-[10px]">
              custom
            </span>
          )}
        </button>

        {showPipeline && (
          <div className="mt-2 flex flex-wrap gap-2 p-3 rounded-xl bg-white/5 border border-white/10">
            {ALL_AGENTS.map((agent) => {
              const checked = selectedAgents.includes(agent)
              return (
                <button
                  key={agent}
                  type="button"
                  onClick={() => toggleAgent(agent)}
                  className={`text-xs px-3 py-1.5 rounded-full border transition-all flex items-center gap-1.5 ${
                    checked
                      ? 'bg-indigo-500/20 border-indigo-400/40 text-indigo-200'
                      : 'bg-white/5 border-white/10 text-white/30'
                  }`}
                >
                  {checked && <span className="w-1 h-1 rounded-full bg-indigo-400" />}
                  {agent}
                </button>
              )
            })}
            <span className="text-xs text-white/20 self-center ml-1">
              ? {orderedSelection.join(' ? ') || 'none'}
            </span>
          </div>
        )}
      </div>

      {error && (
        <p className="mt-3 text-xs text-red-400 bg-red-400/10 border border-red-400/20 rounded-xl px-4 py-2.5">
          ? {error}
        </p>
      )}
    </div>
  )
}
