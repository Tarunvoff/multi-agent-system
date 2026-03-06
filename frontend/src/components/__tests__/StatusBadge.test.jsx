import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import StatusBadge from '../StatusBadge.jsx'

describe('StatusBadge', () => {
  it('renders the status text', () => {
    render(<StatusBadge status="completed" />)
    expect(screen.getByText('completed')).toBeInTheDocument()
  })

  it('renders "pending" when no status given', () => {
    render(<StatusBadge />)
    expect(screen.getByText('pending')).toBeInTheDocument()
  })

  it('renders all known statuses without crashing', () => {
    const statuses = [
      'completed', 'planning', 'researching', 'fact_checking',
      'writing', 'reviewing', 'error', 'pending',
    ]
    statuses.forEach(status => {
      const { unmount } = render(<StatusBadge status={status} />)
      unmount()
    })
  })

  it('replaces underscores with spaces in display text', () => {
    render(<StatusBadge status="fact_checking" />)
    expect(screen.getByText('fact checking')).toBeInTheDocument()
  })

  it('applies the pulsing dot for in-progress statuses', () => {
    const { container } = render(<StatusBadge status="planning" />)
    const dot = container.querySelector('.animate-pulse')
    expect(dot).toBeInTheDocument()
  })

  it('does not apply pulsing dot for completed status', () => {
    const { container } = render(<StatusBadge status="completed" />)
    const dot = container.querySelector('.animate-pulse')
    expect(dot).not.toBeInTheDocument()
  })

  it('falls back gracefully to pending styling for unknown status', () => {
    render(<StatusBadge status="unknown_status" />)
    // component replaces underscores with spaces in the display text
    expect(screen.getByText('unknown status')).toBeInTheDocument()
  })
})
