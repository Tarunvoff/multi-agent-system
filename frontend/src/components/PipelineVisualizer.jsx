import React from 'react'

// SVG icons for each agent — avoids emoji encoding issues across platforms.
const AgentIcon = ({ agent, className = 'w-6 h-6' }) => {
  if (agent === 'planner') return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.8}
        d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
    </svg>
  )
  if (agent === 'researcher') return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.8}
        d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
    </svg>
  )
  if (agent === 'factchecker') return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.8}
        d="M9 12l2 2 4-4M7.835 4.697a3.42 3.42 0 001.946-.806 3.42 3.42 0 014.438 0 3.42 3.42 0 001.946.806 3.42 3.42 0 013.138 3.138 3.42 3.42 0 00.806 1.946 3.42 3.42 0 010 4.438 3.42 3.42 0 00-.806 1.946 3.42 3.42 0 01-3.138 3.138 3.42 3.42 0 00-1.946.806 3.42 3.42 0 01-4.438 0 3.42 3.42 0 00-1.946-.806 3.42 3.42 0 01-3.138-3.138 3.42 3.42 0 00-.806-1.946 3.42 3.42 0 010-4.438 3.42 3.42 0 00.806-1.946 3.42 3.42 0 013.138-3.138z" />
    </svg>
  )
  if (agent === 'writer') return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.8}
        d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
    </svg>
  )
  if (agent === 'reviewer') return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.8}
        d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
    </svg>
  )
  // Unknown agent
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.8}
        d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
    </svg>
  )
}

// Agent display metadata — activeStatus maps to the backend task.status value
// set while this agent is running.
const AGENT_META = {
  planner:     { label: 'Planner',      activeStatus: 'planning',      color: { ring: 'ring-blue-400',    bg: 'bg-blue-50',    text: 'text-blue-700',    glow: 'shadow-blue-100',    icon: 'text-blue-500'    } },
  researcher:  { label: 'Researcher',   activeStatus: 'researching',   color: { ring: 'ring-violet-400',  bg: 'bg-violet-50',  text: 'text-violet-700',  glow: 'shadow-violet-100',  icon: 'text-violet-500'  } },
  factchecker: { label: 'Fact Checker', activeStatus: 'fact_checking', color: { ring: 'ring-cyan-400',    bg: 'bg-cyan-50',    text: 'text-cyan-700',    glow: 'shadow-cyan-100',    icon: 'text-cyan-500'    } },
  writer:      { label: 'Writer',       activeStatus: 'writing',       color: { ring: 'ring-amber-400',   bg: 'bg-amber-50',   text: 'text-amber-700',   glow: 'shadow-amber-100',   icon: 'text-amber-500'   } },
  reviewer:    { label: 'Reviewer',     activeStatus: 'reviewing',     color: { ring: 'ring-emerald-400', bg: 'bg-emerald-50', text: 'text-emerald-700', glow: 'shadow-emerald-100', icon: 'text-emerald-500' } },
}

const DEFAULT_PIPELINE = ['planner', 'researcher', 'writer', 'reviewer']

/**
 * Determine the visual state of a stage based on the task's current status
 * and the agent's position within the ACTUAL pipeline array.
 *
 * Resolution order:
 *   1. If status is completed/error → every stage is "done"
 *   2. If this agent's activeStatus matches current status → "active"
 *   3. Find which pipeline position is currently active; stages before it are "done"
 */
function getStageState(agentName, currentStatus, pipeline) {
  if (currentStatus === 'completed' || currentStatus === 'error') return 'done'

  const meta = AGENT_META[agentName]
  if (meta && meta.activeStatus === currentStatus) return 'active'

  // Find the index of the currently running agent inside this pipeline.
  const activeIdx = pipeline.findIndex(
    name => AGENT_META[name]?.activeStatus === currentStatus
  )
  const myIdx = pipeline.indexOf(agentName)

  if (activeIdx === -1) return 'idle'   // status not tied to any agent in pipeline
  if (myIdx === -1)     return 'idle'   // agent not in pipeline (shouldn't happen)
  return myIdx < activeIdx ? 'done' : 'idle'
}

export default function PipelineVisualizer({ status, pipeline }) {
  if (!status) return null

  const agentNames = pipeline && pipeline.length > 0 ? pipeline : DEFAULT_PIPELINE

  return (
    <div className="bg-white rounded-2xl shadow-sm border border-gray-100 px-6 py-5">
      <div className="flex items-center gap-3 mb-6">
        <span className="text-sm font-semibold text-gray-900">Pipeline</span>
        <span className="text-xs text-gray-400">{agentNames.join(' \u2192 ')}</span>
        {status === 'completed' && (
          <span className="ml-auto inline-flex items-center gap-1.5 text-xs font-medium text-emerald-600">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
            All agents completed
          </span>
        )}
      </div>

      <div className="flex items-start">
        {agentNames.map((agentName, i) => {
          const meta  = AGENT_META[agentName] || {
            label: agentName,
            activeStatus: '',
            color: { ring: 'ring-gray-400', bg: 'bg-gray-50', text: 'text-gray-700', glow: 'shadow-gray-100', icon: 'text-gray-400' },
          }
          const state = getStageState(agentName, status, agentNames)
          const c     = meta.color

          const nextName     = agentNames[i + 1]
          const nextState    = nextName ? getStageState(nextName, status, agentNames) : null
          const connectorLit = nextState !== null && nextState !== 'idle'

          return (
            <React.Fragment key={`${agentName}-${i}`}>
              <div className="flex flex-col items-center gap-2.5 flex-shrink-0">
                <div className={[
                  'relative w-14 h-14 rounded-2xl border-2 flex items-center justify-center transition-all duration-500',
                  state === 'active' ? `${c.bg} border-transparent ring-2 ${c.ring} shadow-lg ${c.glow}` : '',
                  state === 'done'   ? 'bg-emerald-50 border-emerald-200' : '',
                  state === 'idle'   ? 'bg-gray-50 border-gray-100' : '',
                ].join(' ')}>
                  {state === 'done' ? (
                    <svg className="w-7 h-7 text-emerald-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M5 13l4 4L19 7" />
                    </svg>
                  ) : (
                    <AgentIcon
                      agent={agentName}
                      className={`w-6 h-6 ${state === 'idle' ? 'text-gray-300' : c.icon}`}
                    />
                  )}

                  {state === 'active' && (
                    <span className={`absolute inset-[-4px] rounded-[18px] border-2 ${c.ring} animate-ping opacity-20`} />
                  )}
                </div>

                <span className={`text-xs font-medium transition-colors duration-300 ${
                  state === 'active' ? c.text :
                  state === 'done'   ? 'text-emerald-600' :
                                       'text-gray-300'
                }`}>
                  {meta.label}
                </span>
              </div>

              {i < agentNames.length - 1 && (
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
