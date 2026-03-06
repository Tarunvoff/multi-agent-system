import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import PipelineVisualizer from '../PipelineVisualizer.jsx'

describe('PipelineVisualizer', () => {
  it('renders nothing when status is null', () => {
    const { container } = render(<PipelineVisualizer status={null} />)
    expect(container.firstChild).toBeNull()
  })

  it('renders the default 4-agent pipeline when no pipeline prop given', () => {
    render(<PipelineVisualizer status="planning" />)
    expect(screen.getByText('Planner')).toBeInTheDocument()
    expect(screen.getByText('Researcher')).toBeInTheDocument()
    expect(screen.getByText('Writer')).toBeInTheDocument()
    expect(screen.getByText('Reviewer')).toBeInTheDocument()
  })

  it('renders a custom pipeline with factchecker', () => {
    const pipeline = ['planner', 'researcher', 'factchecker', 'writer']
    render(<PipelineVisualizer status="researching" pipeline={pipeline} />)
    expect(screen.getByText('Fact Checker')).toBeInTheDocument()
    expect(screen.queryByText('Reviewer')).not.toBeInTheDocument()
  })

  it('shows "All agents completed" banner when status is completed', () => {
    render(<PipelineVisualizer status="completed" />)
    expect(screen.getByText('All agents completed')).toBeInTheDocument()
  })

  it('shows the agent order in the header', () => {
    const pipeline = ['planner', 'writer']
    render(<PipelineVisualizer status="planning" pipeline={pipeline} />)
    expect(screen.getByText('planner → writer')).toBeInTheDocument()
  })

  it('renders check marks for completed stages', () => {
    // When status is "writing", planner and researcher should be done (checkmarks)
    const { container } = render(
      <PipelineVisualizer status="writing" pipeline={['planner', 'researcher', 'writer', 'reviewer']} />
    )
    // SVG checkmark paths appear for done stages
    const checkPaths = container.querySelectorAll('path[d="M5 13l4 4L19 7"]')
    expect(checkPaths.length).toBeGreaterThanOrEqual(2)
  })

  it('handles unknown agent names gracefully', () => {
    render(<PipelineVisualizer status="planning" pipeline={['planner', 'custom_agent']} />)
    expect(screen.getByText('custom_agent')).toBeInTheDocument()
  })
})
