import pytest

pytestmark = pytest.mark.unit

from unittest.mock import patch, MagicMock
from app.agents.jd_architect import jd_architect_node
from app.agents.screener import screener_node
from app.models.state import PipelineStage, ApprovalStatus, CandidateProfile

@pytest.mark.asyncio
async def test_jd_architect_node_basic(mock_state):
    """Verify JD Architect drafts a structured description."""
    
    # Mock LLM to avoid real calls
    with patch("langchain_openai.ChatOpenAI.astream") as mock_stream:
        # Mock streaming chunks
        mock_stream.return_value.__aiter__.return_value = [
            MagicMock(content="<thought_process>Mock reasoning</thought_process>"),
            MagicMock(content="<job_description># Senior AI Role\nDetailed job description.</job_description>"),
            MagicMock(content="<bias_audit>Bias audit result.</bias_audit>")
        ]
        
        updated_state = await jd_architect_node(mock_state)
        
        # Assertions
        assert updated_state.job_description != ""
        assert updated_state.current_stage == PipelineStage.JD_REVIEW.value
        assert updated_state.jd_approval == ApprovalStatus.PENDING.value
        assert len(updated_state.audit_log) > 0
        assert updated_state.audit_log[-1].agent == "JD Architect"

@pytest.mark.asyncio
async def test_screener_node_scores(mock_state):
    """Verify Screener provides deterministic scores within 0-100 range."""
    
    # Pre-populate state with candidates
    mock_state.candidates = [
        CandidateProfile(name="Alice Smith", skills=["Python", "PyTorch"], experience_years=5)
    ]
    
    # Screener is DETERMINISTIC, no LLM call needed
    updated_state = await screener_node(mock_state)
    
    # Functional assertions
    assert len(updated_state.scored_candidates) == 1
    score = updated_state.scored_candidates[0]
    assert 0 <= score.overall_score <= 100
    assert score.overall_score == 74.2 # (16.7 skill + 25.0 exp + 12.5 edu + 20.0 cultural)
    assert updated_state.current_stage == PipelineStage.SHORTLIST_REVIEW.value

@pytest.mark.asyncio
async def test_agent_error_handling(mock_state):
    """Ensure agent nodes handle LLM errors gracefully without crashing."""
    mock_state.current_stage = PipelineStage.JD_DRAFTING.value
    
    with patch("langchain_openai.ChatOpenAI.astream", side_effect=Exception("LLM Timeout")):
        updated_state = await jd_architect_node(mock_state)
        
        # Self-healing / Error recording
        assert "LLM Error" in updated_state.error
        assert updated_state.current_stage == PipelineStage.JD_DRAFTING.value 
