import React, { useState } from 'react'

const AGENT_CFG = {
  planner:    { label: 'Planner',    border: 'border-blue-400',    dot: 'bg-blue-500',    text: 'text-blue-700',    badge: 'bg-blue-50 text-blue-600'     },
  researcher: { label: 'Researcher', border: 'border-violet-400',  dot: 'bg-violet-500',  text: 'text-violet-700',  badge: 'bg-violet-50 text-violet-600'  },
  writer:     { label: 'Writer',     border: 'border-amber-400',   dot: 'bg-amber-500',   text: 'text-amber-700',   badge: 'bg-amber-50 text-amber-600'    },
  reviewer:   { label: 'Reviewer',   border: 'border-emerald-400', dot: 'bg-emerald-500', text: 'text-emerald-700', badge: 'bg-emerald-50 text-emerald-600' },
}

function formatTime(ts) {
  if (!ts) return ''
  return new Date(ts).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })
}

function formatDuration(ms) {
  if (ms == null) return null
  if (ms < 1000) return `${Math.round(ms)} ms`
  return `${(ms / 1000).toFixed(1)} s`
}

function formatOutput(agent, output) {
  if (agent === 'planner' && Array.isArray(output)) {
    return `Planned ${output.length} subtask${output.length !== 1 ? 's' : ''}: ${output.join(' · ')}`
  }
  if (typeof output === 'string') return output
  return JSON.stringify(output)
}

function StepCard({ step, index }) {
  const [expanded, setExpanded] = useState(false)
  const cfg = AGENT_CFG[step.agent] || {
    label: step.agent, border: 'border-gray-300', dot: 'bg-gray-400',
    text: 'text-gray-700', badge: 'bg-gray-100 text-gray-600',
  }

  const rawOutput = formatOutput(step.agent, step.output)
  const isLong    = rawOutput.length > 130
  const preview   = expanded || !isLong ? rawOutput : rawOutput.slice(0, 130) + '…'
  const duration  = formatDuration(step.duration_ms)

  // Show "Researcher — Early Life" style titles for researcher subtasks
  const title = step.subtask
    ? `${cfg.label} — ${step.subtask}`
    : cfg.label

  return (
    <div
      className={`border-l-2 ${cfg.border} pl-4 py-0.5 animate-slide-up`}
      style={{ animationDelay: `${index * 55}ms` }}
    >
      <div className="flex items-start justify-between gap-2 mb-1">
        <div className="flex items-center gap-2 flex-wrap">
          <span className={`w-1.5 h-1.5 rounded-full shrink-0 mt-0.5 ${cfg.dot}`} />
          <span className={`text-xs font-semibold ${cfg.text}`}>{title}</span>
          {duration && (
            <span className={`text-xs px-1.5 py-0.5 rounded-md font-mono ${cfg.badge}`}>
              {duration}
            </span>
          )}
        </div>
        <span className="text-xs text-gray-300 shrink-0 whitespace-nowrap mt-0.5">
          {formatTime(step.timestamp)}
        </span>
      </div>

      <p className="text-xs text-gray-500 leading-relaxed ml-3.5">{preview}</p>

      {isLong && (
        <button
          onClick={() => setExpanded(v => !v)}
          className="text-xs text-indigo-500 hover:text-indigo-700 ml-3.5 mt-0.5 transition-colors"
        >
          {expanded ? '↑ Less' : '↓ More'}
        </button>
      )}
    </div>
  )
}

export default function Timeline({ steps }) {
  /* Loading skeleton */
  if (!steps || steps.length === 0) {
    return (
      <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
        <h3 className="text-sm font-semibold text-gray-900 mb-4">Execution Timeline</h3>
        <div className="space-y-4">
          {[1, 2, 3].map(i => (
            <div key={i} className="flex gap-3">
              <div className="shimmer w-0.5 rounded-full h-14 shrink-0" />
              <div className="flex-1 space-y-2 pt-1">
                <div className="shimmer h-2.5 rounded-full w-1/3" />
                <div className="shimmer h-2 rounded-full w-full" />
                <div className="shimmer h-2 rounded-full w-4/5" />
              </div>
            </div>
          ))}
        </div>
      </div>
    )
  }

  return (
    <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
      <div className="flex items-center justify-between mb-5">
        <h3 className="text-sm font-semibold text-gray-900">Execution Timeline</h3>
        <span className="text-xs text-gray-400 bg-gray-50 px-2.5 py-0.5 rounded-full border border-gray-100">
          {steps.length} step{steps.length !== 1 ? 's' : ''}
        </span>
      </div>

      <div className="space-y-4">
        {steps.map((step, i) => (
          <StepCard key={i} step={step} index={i} />
        ))}
      </div>
    </div>
  )
}
