import React, { useState } from 'react'
import ReactMarkdown from 'react-markdown'

function wordCount(text) {
  if (!text) return 0
  return text.trim().split(/\s+/).filter(Boolean).length
}

export default function ReportViewer({ result, taskId }) {
  const [copied, setCopied] = useState(false)

  const handleCopy = () => {
    navigator.clipboard.writeText(result)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  const handleDownload = () => {
    const blob = new Blob([result], { type: 'text/markdown' })
    const url  = URL.createObjectURL(blob)
    const a    = document.createElement('a')
    a.href     = url
    a.download = `report-${taskId?.slice(0, 8) || 'output'}.md`
    a.click()
    URL.revokeObjectURL(url)
  }

  /* ── Empty / generating state ────────────────────────────── */
  if (!result) {
    return (
      <div className="bg-white rounded-2xl shadow-sm border border-gray-100 min-h-72 flex flex-col">
        <div className="px-6 py-4 border-b border-gray-100 flex items-center gap-2.5">
          <div className="w-7 h-7 rounded-lg bg-gray-50 flex items-center justify-center">
            <svg className="w-3.5 h-3.5 text-gray-300" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
          </div>
          <span className="text-sm font-semibold text-gray-900">Final Report</span>
        </div>

        <div className="flex-1 flex flex-col items-center justify-center gap-4 px-10 py-12 text-center">
          <div className="w-10 h-10 rounded-xl bg-gray-50 border border-gray-100 flex items-center justify-center">
            <svg className="w-5 h-5 text-gray-300" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
                d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
          </div>
          <div>
            <p className="text-xs font-medium text-gray-400">Generating report…</p>
            <p className="text-xs text-gray-300 mt-0.5">Appears here once the pipeline completes</p>
          </div>
          <div className="w-full max-w-56 space-y-2 mt-1">
            <div className="shimmer h-2.5 rounded-full w-full" />
            <div className="shimmer h-2.5 rounded-full w-5/6" />
            <div className="shimmer h-2.5 rounded-full w-4/6" />
            <div className="shimmer h-2.5 rounded-full w-3/6" />
          </div>
        </div>
      </div>
    )
  }

  const wc      = wordCount(result)
  const readMin = Math.max(1, Math.round(wc / 200))

  return (
    <div className="bg-white rounded-2xl shadow-sm border border-gray-100 flex flex-col animate-slide-up">
      {/* Header */}
      <div className="flex items-center justify-between px-6 py-4 border-b border-gray-100">
        <div className="flex items-center gap-2.5">
          <div className="w-7 h-7 rounded-lg bg-indigo-50 flex items-center justify-center">
            <svg className="w-3.5 h-3.5 text-indigo-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
          </div>
          <span className="text-sm font-semibold text-gray-900">Final Report</span>
        </div>

        <div className="flex items-center gap-2.5">
          <span className="text-xs text-gray-300 hidden sm:block">{wc} words · {readMin} min read</span>
          {taskId && <span className="text-xs text-gray-200 font-mono hidden md:block">{taskId.slice(0, 8)}</span>}

          {/* Download */}
          <button
            onClick={handleDownload}
            title="Download Markdown"
            className="p-1.5 rounded-lg text-gray-400 hover:bg-gray-100 hover:text-gray-600 transition-all"
          >
            <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
            </svg>
          </button>

          {/* Copy */}
          <button
            onClick={handleCopy}
            className={`text-xs px-3 py-1.5 rounded-lg font-medium transition-all ${
              copied
                ? 'bg-emerald-100 text-emerald-700'
                : 'bg-gray-100 hover:bg-gray-200 text-gray-600'
            }`}
          >
            {copied ? (
              <span className="flex items-center gap-1">
                <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M5 13l4 4L19 7" />
                </svg>
                Copied
              </span>
            ) : 'Copy'}
          </button>
        </div>
      </div>

      {/* Body */}
      <div className="overflow-y-auto max-h-[640px] px-6 py-5">
        <div className="report-prose">
          <ReactMarkdown>{result}</ReactMarkdown>
        </div>
      </div>
    </div>
  )
}
