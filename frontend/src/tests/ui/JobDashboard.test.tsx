import { render, screen, fireEvent } from '@testing-library/react'
import JobsPage from '@/app/jobs/page'
import { useJobStore } from '@/store/useJobStore'
import { useWebSocket } from '@/hooks/useWebSocket'
import { useSearchParams } from 'next/navigation'

// Mock state management
jest.mock('@/store/useJobStore')
jest.mock('@/hooks/useWebSocket')
jest.mock('next/navigation')

describe('Jobs Dashboard UI', () => {
  const mockFetchJobsList = jest.fn()
  const mockFetchJobDetails = jest.fn()
  const mockSetCurrentJob = jest.fn()

  beforeEach(() => {
    jest.clearAllMocks()
    ;(useSearchParams as unknown as jest.Mock).mockReturnValue({
      get: jest.fn().mockReturnValue(null),
    })
    ;(useWebSocket as unknown as jest.Mock).mockReturnValue({
      connected: true,
      tokenStream: '',
    })
    ;(useJobStore as unknown as jest.Mock).mockReturnValue({
      jobsList: [
        { job_id: 'job-1', job_title: 'AI Dev', department: 'Eng', current_stage: 'intake' }
      ],
      currentJob: null,
      loading: false,
      fetchJobsList: mockFetchJobsList,
      fetchJobDetails: mockFetchJobDetails,
      setCurrentJob: mockSetCurrentJob,
    })
  })

  test('renders the dashboard header and "New Position" button', () => {
    render(<JobsPage />)
    expect(screen.getByText(/Intelligence Hub/i)).toBeInTheDocument()
    expect(screen.getByText(/New Position/i)).toBeInTheDocument()
  })

  test('calls fetchJobsList on mount', () => {
    render(<JobsPage />)
    expect(mockFetchJobsList).toHaveBeenCalled()
  })

  test('shows the setup form when clicking "New Position"', () => {
    render(<JobsPage />)
    const button = screen.getByText(/New Position/i)
    fireEvent.click(button)
    expect(screen.getByText(/Strategic Requisition Intake/i)).toBeInTheDocument()
  })

  test('selecting a job calls fetchJobDetails', async () => {
    render(<JobsPage />)
    const jobCard = screen.getByText(/AI Dev/i)
    fireEvent.click(jobCard)
    expect(mockFetchJobDetails).toHaveBeenCalledWith('job-1')
  })

  test('renders the pipeline tracker when a job is active', () => {
    // Override store for specific test
    ;(useJobStore as unknown as jest.Mock).mockReturnValue({
      jobsList: [],
      currentJob: { 
        job_id: 'job-1', 
        job_title: 'AI Dev', 
        current_stage: 'jd_review',
        state: { candidates: [], audit_log: [] } 
      },
      loading: false,
      fetchJobsList: mockFetchJobsList,
      fetchJobDetails: mockFetchJobDetails,
    })

    render(<JobsPage />)
    expect(screen.getByText(/Back to List/i)).toBeInTheDocument()
    // Check for PipelineSteps component indirectly by looking for stage labels
    expect(screen.getByText(/Drafting JD/i)).toBeInTheDocument()
  })
})
