import pytest
from unittest.mock import patch, MagicMock, AsyncMock

from evaluation.runner import ExperimentRunner
from evaluation.schemas import SystemVariant, ResultMode
from backend.schemas import AgentStatus, TaskType
from backend.schemas.qa import QAResult, QAFinding
from backend.schemas.enums import FindingSeverity, QAVerdict
from backend.schemas.knowledge import KnowledgeContext, KnowledgeChunk

@pytest.fixture
def runner():
    return ExperimentRunner()

class TestTelemetry:
    @pytest.mark.asyncio
    @patch("evaluation.runner.OllamaClient")
    async def test_llm_call_count_with_retry(self, mock_ollama, runner):
        async def mock_analysis_execute(input_val):
            llm = mock_analysis_execute.agent.llm
            # the agent has the TelemetryLLMClient wrapper
            await llm.generate_structured_output("sys", "user", MagicMock())
            await llm.generate_structured_output("sys", "user", MagicMock())
            await llm.generate_structured_output("sys", "user", MagicMock())
            out = MagicMock()
            out.status = AgentStatus.SUCCESS
            out.result = {}
            return out
            
        with patch("evaluation.runner.AnalysisAgent") as mock_a, \
             patch("evaluation.runner.PlanningAgent") as mock_p, \
             patch("evaluation.runner.SupervisorAgent") as mock_s, \
             patch("evaluation.runner.Retriever") as mock_r_cls, \
             patch("evaluation.runner.EmbeddingClient"):
            
            def mock_analysis_init(*args, **kwargs):
                mock_a.return_value.llm = kwargs.get("llm_client")
                mock_a.return_value.rag_service = kwargs.get("rag_service")
                return mock_a.return_value
            mock_a.side_effect = mock_analysis_init
            
            mock_a.return_value.execute = AsyncMock(side_effect=mock_analysis_execute)
            mock_analysis_execute.agent = mock_a.return_value
            
            mock_p.return_value.execute = AsyncMock()
            mock_p.return_value.execute.return_value.status = AgentStatus.SUCCESS
            mock_s.return_value.execute = AsyncMock()
            mock_s.return_value.execute.return_value.status = AgentStatus.SUCCESS
            mock_s.return_value.execute.return_value.result = {}
            
            mock_ollama.return_value.generate_structured_output = AsyncMock()
            mock_r_cls.return_value.retrieve = AsyncMock()
            mock_r_cls.return_value.retrieve.return_value = KnowledgeContext(query="", chunks=[], total_results=0, retrieval_time_ms=0)
            
            result = await runner.run("ecommerce-catalog", SystemVariant.FULL_SYSTEM, ResultMode.REAL)
            
            assert result.llm_calls == 3

    @pytest.mark.asyncio
    @patch("evaluation.runner.OllamaClient")
    async def test_qa_metrics_extraction(self, mock_ollama, runner):
        with patch("evaluation.runner.AnalysisAgent") as mock_a, \
             patch("evaluation.runner.PlanningAgent") as mock_p, \
             patch("evaluation.runner.SupervisorAgent") as mock_s, \
             patch("evaluation.runner.Retriever") as mock_r_cls, \
             patch("evaluation.runner.EmbeddingClient"):
             
            mock_r_cls.return_value.retrieve = AsyncMock()
            mock_r_cls.return_value.retrieve.return_value = KnowledgeContext(query="", chunks=[], total_results=0, retrieval_time_ms=0)
            
            mock_a.return_value.execute = AsyncMock()
            mock_a.return_value.execute.return_value.status = AgentStatus.SUCCESS
            mock_p.return_value.execute = AsyncMock()
            mock_p.return_value.execute.return_value.status = AgentStatus.SUCCESS
            
            qa_result = {
                "score": 0.75,
                "findings": [
                    {"severity": FindingSeverity.CRITICAL},
                    {"severity": "major"},
                    {"severity": "major"},
                    {"severity": "minor"},
                    {"severity": "minor"},
                    {"severity": "minor"},
                ]
            }
            qa_task = MagicMock()
            qa_task.type = TaskType.QA
            
            qa_agent_out = MagicMock()
            qa_agent_out.result = qa_result
            
            mock_s.return_value.execute = AsyncMock()
            mock_s.return_value.execute.return_value.status = AgentStatus.SUCCESS
            mock_s.return_value.execute.return_value.result = {
                "tasks": {"t1": qa_task},
                "agent_outputs": {"t1": qa_agent_out}
            }
            
            result = await runner.run("ecommerce-catalog", SystemVariant.FULL_SYSTEM, ResultMode.REAL)
            
            assert result.qa_score == 0.75
            assert result.defect_counts.critical == 1
            assert result.defect_counts.major == 2
            assert result.defect_counts.minor == 3

    @pytest.mark.asyncio
    @patch("evaluation.runner.OllamaClient")
    async def test_missing_qa_result(self, mock_ollama, runner):
        with patch("evaluation.runner.AnalysisAgent") as mock_a, \
             patch("evaluation.runner.PlanningAgent") as mock_p, \
             patch("evaluation.runner.SupervisorAgent") as mock_s, \
             patch("evaluation.runner.Retriever") as mock_r_cls, \
             patch("evaluation.runner.EmbeddingClient"):
             
            mock_r_cls.return_value.retrieve = AsyncMock()
            mock_r_cls.return_value.retrieve.return_value = KnowledgeContext(query="", chunks=[], total_results=0, retrieval_time_ms=0)
             
            mock_a.return_value.execute = AsyncMock()
            mock_a.return_value.execute.return_value.status = AgentStatus.SUCCESS
            mock_p.return_value.execute = AsyncMock()
            mock_p.return_value.execute.return_value.status = AgentStatus.SUCCESS
            
            mock_s.return_value.execute = AsyncMock()
            mock_s.return_value.execute.return_value.status = AgentStatus.SUCCESS
            mock_s.return_value.execute.return_value.result = {}
            
            result = await runner.run("ecommerce-catalog", SystemVariant.FULL_SYSTEM, ResultMode.REAL)
            
            assert result.qa_score is None

    @pytest.mark.asyncio
    @patch("evaluation.runner.OllamaClient")
    async def test_rag_enabled_with_chunks(self, mock_ollama, runner):
        with patch("evaluation.runner.AnalysisAgent") as mock_a, \
             patch("evaluation.runner.PlanningAgent") as mock_p, \
             patch("evaluation.runner.SupervisorAgent") as mock_s, \
             patch("evaluation.runner.Retriever") as mock_retriever_cls, \
             patch("evaluation.runner.EmbeddingClient"):
             
            def mock_analysis_init(*args, **kwargs):
                mock_a.return_value.rag_service = kwargs.get("rag_service")
                return mock_a.return_value
            mock_a.side_effect = mock_analysis_init
            
            mock_a.return_value.execute = AsyncMock()
            mock_a.return_value.execute.return_value.status = AgentStatus.SUCCESS
            mock_p.return_value.execute = AsyncMock()
            mock_p.return_value.execute.return_value.status = AgentStatus.SUCCESS
            mock_s.return_value.execute = AsyncMock()
            mock_s.return_value.execute.return_value.status = AgentStatus.SUCCESS
            mock_s.return_value.execute.return_value.result = {}
            
            mock_retriever = mock_retriever_cls.return_value
            mock_retriever.retrieve = AsyncMock()
            mock_retriever.retrieve.return_value = KnowledgeContext(
                query="test", chunks=[KnowledgeChunk(content="a", similarity_score=0.9, source="test")]*2, total_results=2, retrieval_time_ms=100
            )
            
            async def mock_analysis_execute_rag(input_val):
                rag = mock_analysis_execute_rag.agent.rag_service
                await rag.retrieve("test")
                out = MagicMock()
                out.status = AgentStatus.SUCCESS
                out.result = {}
                return out
                
            mock_a.return_value.execute = AsyncMock(side_effect=mock_analysis_execute_rag)
            mock_analysis_execute_rag.agent = mock_a.return_value
            
            result = await runner.run("ecommerce-catalog", SystemVariant.FULL_SYSTEM, ResultMode.REAL)
            
            assert result.rag_used is True
            assert result.rag_retrievals == 1
            assert result.rag_successes == 1
            assert result.chunks_retrieved == 2
            assert result.knowledge_reused is True

    @pytest.mark.asyncio
    @patch("evaluation.runner.OllamaClient")
    async def test_rag_enabled_zero_chunks(self, mock_ollama, runner):
        with patch("evaluation.runner.AnalysisAgent") as mock_a, \
             patch("evaluation.runner.PlanningAgent") as mock_p, \
             patch("evaluation.runner.SupervisorAgent") as mock_s, \
             patch("evaluation.runner.Retriever") as mock_retriever_cls, \
             patch("evaluation.runner.EmbeddingClient"):
             
            def mock_analysis_init(*args, **kwargs):
                mock_a.return_value.rag_service = kwargs.get("rag_service")
                return mock_a.return_value
            mock_a.side_effect = mock_analysis_init
            
            mock_retriever = mock_retriever_cls.return_value
            mock_retriever.retrieve = AsyncMock()
            mock_retriever.retrieve.return_value = KnowledgeContext(query="test", chunks=[], total_results=0, retrieval_time_ms=50)
            
            async def mock_analysis_execute_rag(input_val):
                rag = mock_analysis_execute_rag.agent.rag_service
                await rag.retrieve("test")
                out = MagicMock()
                out.status = AgentStatus.SUCCESS
                return out
                
            mock_a.return_value.execute = AsyncMock(side_effect=mock_analysis_execute_rag)
            mock_analysis_execute_rag.agent = mock_a.return_value
            
            mock_p.return_value.execute = AsyncMock()
            mock_p.return_value.execute.return_value.status = AgentStatus.SUCCESS
            mock_s.return_value.execute = AsyncMock()
            mock_s.return_value.execute.return_value.status = AgentStatus.SUCCESS
            mock_s.return_value.execute.return_value.result = {}
            
            result = await runner.run("ecommerce-catalog", SystemVariant.FULL_SYSTEM, ResultMode.REAL)
            
            assert result.rag_used is True
            assert result.rag_retrievals == 1
            assert result.chunks_retrieved == 0
            assert result.knowledge_reused is False

    @pytest.mark.asyncio
    @patch("evaluation.runner.OllamaClient")
    async def test_rag_disabled(self, mock_ollama, runner):
        with patch("evaluation.runner.AnalysisAgent") as mock_a, \
             patch("evaluation.runner.PlanningAgent") as mock_p, \
             patch("evaluation.runner.SupervisorAgent") as mock_s, \
             patch("evaluation.runner.Retriever") as mock_retriever_cls:
             
            mock_a.return_value.execute = AsyncMock()
            mock_a.return_value.execute.return_value.status = AgentStatus.SUCCESS
            mock_p.return_value.execute = AsyncMock()
            mock_p.return_value.execute.return_value.status = AgentStatus.SUCCESS
            mock_s.return_value.execute = AsyncMock()
            mock_s.return_value.execute.return_value.status = AgentStatus.SUCCESS
            mock_s.return_value.execute.return_value.result = {}
            
            result = await runner.run("ecommerce-catalog", SystemVariant.BASELINE_C_NO_RAG, ResultMode.REAL)
            
            assert result.rag_used is False
            assert result.rag_retrievals == 0
            assert result.chunks_retrieved == 0
            assert result.knowledge_reused is False
