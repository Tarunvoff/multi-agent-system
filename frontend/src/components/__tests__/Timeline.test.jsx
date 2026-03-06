import { render, screen, fireEvent } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import Timeline from '../Timeline.jsx'

const SAMPLE_STEPS = [
  {
    agent: 'planner',
    output: ['subtask one', 'subtask two', 'subtask three'],
    timestamp: '2026-03-06T10:00:00.000Z',
    duration_ms: 320,
  },
  {
    agent: 'researcher',
    subtask: 'subtask one',
    output: { topic: 'subtask one', facts: ['fact A', 'fact B', 'fact C'] },
    timestamp: '2026-03-06T10:00:01.000Z',
    duration_ms: 1400,
  },
  {
    agent: 'writer',
    output: 'Draft created',
    timestamp: '2026-03-06T10:00:03.000Z',
    duration_ms: 2100,
  },
  {
    agent: 'reviewer',
    output: 'approved',
    timestamp: '2026-03-06T10:00:05.000Z',
    duration_ms: 500,
  },
]

describe('Timeline', () => {
  it('renders shimmer placeholders when no steps', () => {
    const { container } = render(<Timeline steps={[]} />)
    const shimmerEls = container.querySelectorAll('.shimmer')
    expect(shimmerEls.length).toBeGreaterThan(0)
  })

  it('renders a step card for each step', () => {
    render(<Timeline steps={SAMPLE_STEPS} />)
    // All four agent labels should appear
    expect(screen.getByText('Planner')).toBeInTheDocument()
    expect(screen.getByText(/Researcher/)).toBeInTheDocument()
    expect(screen.getByText('Writer')).toBeInTheDocument()
    expect(screen.getByText('Reviewer')).toBeInTheDocument()
  })

  it('shows formatted duration badge', () => {
    render(<Timeline steps={SAMPLE_STEPS} />)
    // Planner is 320 ms
    expect(screen.getByText('320 ms')).toBeInTheDocument()
    // Writer is 2.1 s
    expect(screen.getByText('2.1 s')).toBeInTheDocument()
  })

  it('shows step count badge', () => {
    render(<Timeline steps={SAMPLE_STEPS} />)
    expect(screen.getByText('4 steps')).toBeInTheDocument()
  })

  it('shows subtask label on researcher steps', () => {
    render(<Timeline steps={SAMPLE_STEPS} />)
    // The researcher step title includes the subtask name: "Researcher — subtask one"
    expect(screen.getByText('Researcher — subtask one')).toBeInTheDocument()
  })

  it('expands long output on toggle', () => {
    const longStep = {
      ...SAMPLE_STEPS[2],
      output: 'A'.repeat(200),
    }
    render(<Timeline steps={[longStep]} />)
    const moreButton = screen.getByText('↓ More')
    fireEvent.click(moreButton)
    expect(screen.getByText('↑ Less')).toBeInTheDocument()
  })

  it('formats planner output as subtask summary', () => {
    render(<Timeline steps={[SAMPLE_STEPS[0]]} />)
    expect(screen.getByText(/Planned 3 subtasks/)).toBeInTheDocument()
  })
})
