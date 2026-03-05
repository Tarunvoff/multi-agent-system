import React from 'react'

function Stat({ value, label, icon, colors }) {
  return (
    <div className={`flex items-center gap-4 p-5 rounded-2xl border ${colors.border} ${colors.bg}`}>
      <div className={`w-11 h-11 rounded-xl ${colors.iconBg} flex items-center justify-center flex-shrink-0`}>
        {icon}
      </div>
      <div>
        <p className={`text-2xl font-bold leading-none ${colors.value}`}>{value}</p>
        <p className="text-xs text-gray-500 mt-1">{label}</p>
      </div>
    </div>
  )
}

export default function MetricsCard({ metrics }) {
  if (!metrics) return null

  const durationSec = ((metrics.duration_ms ?? 0) / 1000).toFixed(1)

  return (
    <div className="animate-slide-up">
      <div className="flex items-center gap-2 mb-3">
        <span className="text-sm font-semibold text-gray-900">Execution Metrics</span>
        <span className="text-xs text-gray-400">Pipeline performance summary</span>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <Stat
          value={metrics.llm_calls ?? 0}
          label="LLM Calls"
          colors={{ border: 'border-blue-100', bg: 'bg-blue-50/40', iconBg: 'bg-blue-100', value: 'text-blue-700' }}
          icon={
            <svg className="w-5 h-5 text-blue-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.8}
                d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-3 3v-3z" />
            </svg>
          }
        />
        <Stat
          value={metrics.retries ?? 0}
          label="Retries"
          colors={{ border: 'border-amber-100', bg: 'bg-amber-50/40', iconBg: 'bg-amber-100', value: 'text-amber-700' }}
          icon={
            <svg className="w-5 h-5 text-amber-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.8}
                d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
          }
        />
        <Stat
          value={`${durationSec}s`}
          label="Total Duration"
          colors={{ border: 'border-emerald-100', bg: 'bg-emerald-50/40', iconBg: 'bg-emerald-100', value: 'text-emerald-700' }}
          icon={
            <svg className="w-5 h-5 text-emerald-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.8}
                d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          }
        />
      </div>
    </div>
  )
}
