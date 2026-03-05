import React, { useState } from 'react'
import TaskInput from '../components/TaskInput.jsx'
import PipelineVisualizer from '../components/PipelineVisualizer.jsx'
import Timeline from '../components/Timeline.jsx'
import ReportViewer from '../components/ReportViewer.jsx'
import StatusBadge from '../components/StatusBadge.jsx'
import MetricsCard from '../components/MetricsCard.jsx'
import { useTaskPolling } from '../hooks/useTaskPolling.js'

const EXAMPLE_QUERIES = [
  'Compare microservices vs monoliths',
  'History of the Roman Empire',
  'How does GPT-4 work?',
  'Climate change solutions 2025',
]

const AGENTS = [
  { emoji: '🧠', label: 'Planner',    desc: 'Breaks topic into focused subtasks',   from: 'from-blue-500/10'    },
  { emoji: '🔍', label: 'Researcher', desc: 'Gathers facts in parallel threads',    from: 'from-violet-500/10'  },
  { emoji: '✍️', label: 'Writer',     desc: 'Composes a structured report',         from: 'from-amber-500/10'   },
  { emoji: '✅', label: 'Reviewer',   desc: 'Validates quality & flags revisions',  from: 'from-emerald-500/10' },
]

export default function Dashboard() {
  const [taskId, setTaskId]                 = useState(null)
  const [immediateTask, setImmediateTask]   = useState(null)
  const [suggestedQuery, setSuggestedQuery] = useState('')
  const { task: polledTask, error }         = useTaskPolling(taskId)
  const task = polledTask || immediateTask

  const handleTaskStarted = (taskData) => {
    setImmediateTask(taskData)
    setTaskId(taskData.id)
  }

  const handleReset = () => {
    setTaskId(null)
    setImmediateTask(null)
    setSuggestedQuery('')
  }

  /* ── HERO (no active task) ─────────────────────────────────── */
  if (!task) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-950 via-indigo-950 to-slate-900 animate-gradient-x flex flex-col">

        {/* Nav */}
        <nav className="px-8 py-5 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-xl bg-indigo-500 flex items-center justify-center shadow-lg shadow-indigo-900/50">
              <svg className="w-4 h-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                  d="M9 3H5a2 2 0 00-2 2v4m6-6h10a2 2 0 012 2v4M9 3v18m0 0h10a2 2 0 002-2V9M9 21H5a2 2 0 01-2-2V9m0 0h18" />
              </svg>
            </div>
            <span className="text-sm font-semibold text-white/80">Multi-Agent Orchestration</span>
          </div>
          <span className="text-xs text-white/25 hidden sm:block">Planner · Researcher · Writer · Reviewer</span>
        </nav>

        {/* Hero */}
        <div className="flex-1 flex flex-col items-center justify-center px-6 pb-16 text-center">

          {/* Pipeline pill */}
          <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-indigo-500/15 border border-indigo-400/25 mb-8 animate-fade-in">
            <span className="w-1.5 h-1.5 rounded-full bg-indigo-400 animate-pulse" />
            <span className="text-xs text-indigo-300 font-medium">4-agent deterministic pipeline</span>
          </div>

          {/* Headline */}
          <h1 className="text-4xl sm:text-5xl font-bold text-white mb-4 tracking-tight animate-slide-up">
            AI Research,
            <span className="block bg-gradient-to-r from-indigo-400 to-violet-400 bg-clip-text text-transparent">
              fully automated
            </span>
          </h1>

          <p className="text-sm text-white/45 max-w-lg mb-10 animate-slide-up" style={{ animationDelay: '80ms' }}>
            Submit any question. Four specialized agents collaborate — planning, researching, writing, and reviewing — to produce a validated, structured report.
          </p>

          {/* Input */}
          <div className="w-full max-w-2xl animate-slide-up" style={{ animationDelay: '150ms' }}>
            <TaskInput onTaskStarted={handleTaskStarted} initialQuery={suggestedQuery} />
          </div>

          {/* Example chips */}
          <div className="mt-5 flex flex-wrap gap-2 justify-center animate-fade-in" style={{ animationDelay: '250ms' }}>
            <span className="text-xs text-white/25 self-center mr-1">Try:</span>
            {EXAMPLE_QUERIES.map(q => (
              <button
                key={q}
                onClick={() => setSuggestedQuery(q)}
                className="text-xs px-3 py-1.5 rounded-full bg-white/5 border border-white/10 text-white/45
                           hover:bg-white/10 hover:text-white/75 hover:border-white/25 transition-all"
              >
                {q}
              </button>
            ))}
          </div>

          {/* Agent feature cards */}
          <div className="mt-16 grid grid-cols-2 sm:grid-cols-4 gap-3 max-w-xl w-full animate-fade-in" style={{ animationDelay: '350ms' }}>
            {AGENTS.map((a, i) => (
              <div
                key={a.label}
                className={`flex flex-col items-center gap-2 p-4 rounded-2xl bg-gradient-to-b ${a.from} to-transparent border border-white/8 text-center`}
                style={{ animationDelay: `${350 + i * 60}ms` }}
              >
                <span className="text-2xl">{a.emoji}</span>
                <span className="text-xs font-semibold text-white/70">{a.label}</span>
                <span className="text-xs text-white/30 leading-snug">{a.desc}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    )
  }

  /* ── TASK ACTIVE ────────────────────────────────────────────── */
  return (
    <div className="min-h-screen bg-slate-50 font-sans">

      {/* Sticky header */}
      <header className="bg-slate-950 border-b border-white/5 sticky top-0 z-20 shadow-xl">
        <div className="max-w-7xl mx-auto px-5 py-3 flex items-center gap-3">

          {/* Logo */}
          <div className="flex items-center gap-2 shrink-0">
            <div className="w-7 h-7 rounded-lg bg-indigo-500 flex items-center justify-center">
              <svg className="w-3.5 h-3.5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                  d="M9 3H5a2 2 0 00-2 2v4m6-6h10a2 2 0 012 2v4M9 3v18m0 0h10a2 2 0 002-2V9M9 21H5a2 2 0 01-2-2V9m0 0h18" />
              </svg>
            </div>
            <span className="text-xs font-semibold text-white/70 hidden sm:block">Multi-Agent</span>
          </div>

          {/* Query chip */}
          <div className="flex-1 min-w-0 flex items-center gap-2">
            <span className="text-xs text-white/25 shrink-0">Query</span>
            <span className="text-xs text-white/65 font-medium truncate bg-white/5 px-3 py-1 rounded-full border border-white/10">
              {task.query}
            </span>
          </div>

          {/* Controls */}
          <div className="flex items-center gap-2.5 shrink-0">
            <StatusBadge status={task.status} />
            {task.total_duration_ms != null && task.status === 'completed' && (
              <span className="text-xs text-white/30">
                ⏱ {(task.total_duration_ms / 1000).toFixed(1)}s
              </span>
            )}
            <button
              onClick={handleReset}
              className="text-xs px-3 py-1.5 rounded-lg text-white/45 border border-white/10
                         hover:bg-white/8 hover:text-white/75 transition-all"
            >
              ← New task
            </button>
          </div>
        </div>
      </header>

      {/* Error banner */}
      {error && (
        <div className="bg-red-700/10 border-b border-red-500/20 px-6 py-2 text-xs text-red-400 text-center">
          ⚠ {error}
        </div>
      )}

      {/* Main */}
      <main className="max-w-7xl mx-auto px-5 py-6 space-y-5 animate-fade-in">

        {/* Pipeline */}
        <PipelineVisualizer status={task.status} />

        {/* Timeline (2/5) + Report (3/5) */}
        <div className="grid grid-cols-1 lg:grid-cols-5 gap-5 items-start">
          <div className="lg:col-span-2">
            <Timeline steps={task.steps} />
          </div>
          <div className="lg:col-span-3">
            <ReportViewer result={task.result} taskId={task.id} />
          </div>
        </div>

        {/* Metrics — shown only after completion */}
        {task.status === 'completed' && task.metrics && (
          <MetricsCard metrics={task.metrics} />
        )}
      </main>
    </div>
  )
}
