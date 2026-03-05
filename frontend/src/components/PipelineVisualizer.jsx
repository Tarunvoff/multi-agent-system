import React from 'react'

const STAGES = [
  { key: 'planning',    label: 'Planner',    emoji: '🧠', color: { ring: 'ring-blue-400',    bg: 'bg-blue-50',    text: 'text-blue-700',    glow: 'shadow-blue-100'    } },
  { key: 'researching', label: 'Researcher', emoji: '🔍', color: { ring: 'ring-violet-400',  bg: 'bg-violet-50',  text: 'text-violet-700',  glow: 'shadow-violet-100'  } },
  { key: 'writing',     label: 'Writer',     emoji: '✍️', color: { ring: 'ring-amber-400',   bg: 'bg-amber-50',   text: 'text-amber-700',   glow: 'shadow-amber-100'   } },
  { key: 'reviewing',   label: 'Reviewer',   emoji: '✅', color: { ring: 'ring-emerald-400', bg: 'bg-emerald-50', text: 'text-emerald-700', glow: 'shadow-emerald-100' } },
]

const PIPELINE = ['planning', 'researching', 'writing', 'reviewing', 'completed']

function getState(stageKey, currentStatus) {
  if (currentStatus === 'completed') return 'done'
  const ci = PIPELINE.indexOf(currentStatus)
  const si = PIPELINE.indexOf(stageKey)
  if (si < ci) return 'done'
  if (si === ci) return 'active'
  return 'idle'
}

export default function PipelineVisualizer({ status }) {
  if (!status) return null

  return (
    <div className="bg-white rounded-2xl shadow-sm border border-gray-100 px-6 py-5">
      <div className="flex items-center gap-3 mb-6">
        <span className="text-sm font-semibold text-gray-900">Pipeline</span>
        <span className="text-xs text-gray-400">Agent workflow</span>
        {status === 'completed' && (
          <span className="ml-auto inline-flex items-center gap-1.5 text-xs font-medium text-emerald-600">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
            All agents completed
          </span>
        )}
      </div>

      <div className="flex items-start">
        {STAGES.map((stage, i) => {
          const state     = getState(stage.key, status)
          const c         = stage.color
          const nextState = i < STAGES.length - 1 ? getState(STAGES[i + 1].key, status) : null
          const connectorLit = nextState !== null && nextState !== 'idle'

          return (
            <React.Fragment key={stage.key}>
              {/* Stage node */}
              <div className="flex flex-col items-center gap-2.5 flex-shrink-0">
                <div className={`
                  relative w-14 h-14 rounded-2xl border-2 flex items-center justify-center text-2xl
                  transition-all duration-500
                  ${state === 'active' ? `${c.bg} border-transparent ring-2 ${c.ring} shadow-lg ${c.glow}` : ''}
                  ${state === 'done'   ? 'bg-emerald-50 border-emerald-200' : ''}
                  ${state === 'idle'   ? 'bg-gray-50 border-gray-100' : ''}
                `}>
                  {state === 'done' ? (
                    <svg className="w-7 h-7 text-emerald-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M5 13l4 4L19 7" />
                    </svg>
                  ) : (
                    <span className={state === 'idle' ? 'grayscale opacity-30' : ''}>{stage.emoji}</span>
                  )}

                  {/* Pulsing ring for active stage */}
                  {state === 'active' && (
                    <span className={`absolute inset-[-4px] rounded-[18px] border-2 ${c.ring} animate-ping opacity-20`} />
                  )}
                </div>

                <span className={`text-xs font-medium transition-colors duration-300 ${
                  state === 'active' ? c.text :
                  state === 'done'   ? 'text-emerald-600' :
                                       'text-gray-300'
                }`}>
                  {stage.label}
                </span>
              </div>

              {/* Connector arrow */}
              {i < STAGES.length - 1 && (
                <div className="flex-1 flex items-center mt-7 px-1 min-w-6">
                  <div
                    className="h-px flex-1 transition-colors duration-700"
                    style={{ backgroundColor: connectorLit ? '#6ee7b7' : '#f1f5f9' }}
                  />
                  <svg
                    className="w-3 h-3 -ml-px flex-shrink-0 transition-colors duration-700"
                    style={{ color: connectorLit ? '#34d399' : '#e2e8f0' }}
                    fill="none" viewBox="0 0 24 24" stroke="currentColor"
                  >
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M9 5l7 7-7 7" />
                  </svg>
                </div>
              )}
            </React.Fragment>
          )
        })}
      </div>
    </div>
  )
}
