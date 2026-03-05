import React from 'react'

const STATUS = {
  completed:   { pill: 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/25', dot: 'bg-emerald-400' },
  planning:    { pill: 'bg-blue-500/15    text-blue-400    border border-blue-500/25',    dot: 'bg-blue-400 animate-pulse' },
  researching: { pill: 'bg-violet-500/15  text-violet-400  border border-violet-500/25',  dot: 'bg-violet-400 animate-pulse' },
  writing:     { pill: 'bg-amber-500/15   text-amber-400   border border-amber-500/25',    dot: 'bg-amber-400 animate-pulse' },
  reviewing:   { pill: 'bg-orange-500/15  text-orange-400  border border-orange-500/25',  dot: 'bg-orange-400 animate-pulse' },
  error:       { pill: 'bg-red-500/15     text-red-400     border border-red-500/25',      dot: 'bg-red-400' },
  pending:     { pill: 'bg-white/5        text-white/40    border border-white/10',        dot: 'bg-white/30' },
}

export default function StatusBadge({ status }) {
  const key = status?.toLowerCase() || 'pending'
  const s   = STATUS[key] || STATUS.pending

  return (
    <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium capitalize ${s.pill}`}>
      <span className={`w-1.5 h-1.5 rounded-full flex-shrink-0 ${s.dot}`} />
      {status || 'pending'}
    </span>
  )
}

