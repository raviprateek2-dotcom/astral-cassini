import pytest
from unittest.mock import patch, MagicMock
from app.rag.embeddings import index_resume, search_resumes, get_collection_count
from langchain_core.documents import Document

@patch("app.rag.embeddings._get_vectorstore")
@patch("app.rag.embeddings._save_vectorstore")
def test_index_resume_adds_documents(mock_save, mock_get_vs):
    mock_vs = MagicMock()
    mock_get_vs.return_value = mock_vs

    parsed = {
        "id": "cand-123",
        "name": "Alice",
        "email": "alice@test.com",
        "skills": ["Python", "AWS"],
        "experience_years": 5,
        "education": "BS CS",
        "chunks": [
            {"section": "experience", "text": "Worked at Google."}
        ]
    }
    
    cand_id = index_resume(parsed)
    assert cand_id == "cand-123"
    
    mock_vs.add_documents.assert_called_once()
    docs = mock_vs.add_documents.call_args[0][0]
    assert len(docs) == 1
    assert docs[0].page_content == "Worked at Google."
    assert docs[0].metadata["candidate_id"] == "cand-123"
    
    mock_save.assert_called_once()


@patch("app.rag.embeddings._get_vectorstore")
def test_search_resumes_returns_ranked_results(mock_get_vs):
    mock_vs = MagicMock()
    mock_get_vs.return_value = mock_vs
    
    mock_vs.similarity_search_with_relevance_scores.return_value = [
        (Document(page_content="Experience with AWS", metadata={"candidate_id": "c1", "candidate_name": "Bob", "skills": "AWS", "experience_years": 3}), 0.8),
        (Document(page_content="Python dev", metadata={"candidate_id": "c2", "candidate_name": "Charlie", "skills": "Python", "experience_years": 5}), 0.6)
    ]
    
    results = search_resumes("AWS developer", k=2, min_experience_years=0)
    
    assert len(results) == 2
    assert results[0]["id"] == "c1"
    assert results[0]["name"] == "Bob"
    assert results[1]["id"] == "c2"

@patch("app.rag.embeddings._get_vectorstore")
def test_search_resumes_fallback_behavior(mock_get_vs):
    mock_vs = MagicMock()
    mock_vs.similarity_search_with_relevance_scores.side_effect = Exception("FAISS loading error")
    mock_get_vs.return_value = mock_vs
    
    results = search_resumes("AWS developer", k=2)
    assert results == []

@patch("app.rag.embeddings._vectorstore")
def test_get_collection_count(mock_vectorstore):
    with patch("app.rag.embeddings._vectorstore", None):
        count = get_collection_count()
        assert count == 0
