import { render, screen, fireEvent } from '@testing-library/react'
import { CandidateTable } from '@/components/CandidateTable'

describe('CandidateTable Component', () => {
  const mockCandidates = [
    { 
        candidate_id: '1', 
        candidate_name: 'John Doe', 
        overall_score: 85, 
        skills_match: 22, 
        experience_match: 21,
        match_reason: 'Strong Python background.' 
    },
    { 
        candidate_id: '2', 
        candidate_name: 'Jane Smith', 
        overall_score: 92, 
        skills_match: 24, 
        experience_match: 23,
        match_reason: 'Expert ML researcher.' 
    }
  ]
  const mockOnRowClick = jest.fn()

  test('renders multiple rows based on candidate list', () => {
    render(<CandidateTable candidates={mockCandidates} onRowClick={mockOnRowClick} stage="sourcing" />)
    expect(screen.getByText('John Doe')).toBeInTheDocument()
    expect(screen.getByText('Jane Smith')).toBeInTheDocument()
  })

  test('displays correct scores for each candidate', () => {
    render(<CandidateTable candidates={mockCandidates} onRowClick={mockOnRowClick} stage="sourcing" />)
    expect(screen.getByText('85')).toBeInTheDocument()
    expect(screen.getByText('92')).toBeInTheDocument()
  })

  test('triggers callback when a row is clicked', () => {
    render(<CandidateTable candidates={mockCandidates} onRowClick={mockOnRowClick} stage="sourcing" />)
    const johnRow = screen.getByText('John Doe').closest('tr')
    fireEvent.click(johnRow!)
    expect(mockOnRowClick).toHaveBeenCalledWith(expect.objectContaining({
        candidate_id: '1',
        candidate_name: 'John Doe'
    }))
  })

  test('sorting by score changes row order', () => {
    render(<CandidateTable candidates={mockCandidates} onRowClick={mockOnRowClick} stage="sourcing" />)
    const scoreHeader = screen.getByText(/Score/i)
    
    // Initial order is DESCENDING by score (Jane 92, John 85)
    let rows = screen.getAllByRole('row').slice(1) // Skip header
    expect(rows[0]).toHaveTextContent('Jane Smith')
    
    // 1st click: sets sortField to "score", sortDesc remains true (Descending)
    fireEvent.click(scoreHeader)
    
    // 2nd click: toggles sortDesc to false (Ascending)
    fireEvent.click(scoreHeader)
    
    // John (85) should now be first 
    rows = screen.getAllByRole('row').slice(1)
    expect(rows[0]).toHaveTextContent('John Doe')
  })
})
