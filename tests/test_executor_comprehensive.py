"""Comprehensive tests for PAL executor system to improve coverage."""

import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from pal.core.executor import (
    AnthropicClient,
    MockLLMClient,
    OpenAIClient,
    PromptExecutor,
)
from pal.exceptions.core import PALExecutorError
from pal.models.schema import PromptAssembly


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_prompt_assembly():
    """Create a sample prompt assembly."""
    return PromptAssembly(
        id="test-prompt",
        version="1.0.0",
        description="Test prompt",
        variables=[],
        composition=["Test prompt content"],
    )


class TestOpenAIClient:
    """Test OpenAI client with various scenarios."""

    def test_openai_client_import_error(self):
        """Test OpenAI client when package is not available."""
        with (
            patch.dict("sys.modules", {"openai": None}),
            patch(
                "builtins.__import__",
                side_effect=ImportError("No module named 'openai'"),
            ),
        ):
            with pytest.raises(PALExecutorError) as exc_info:
                OpenAIClient()
            assert "OpenAI package not installed" in str(exc_info.value)


class TestAnthropicClient:
    """Test Anthropic client with various scenarios."""

    def test_anthropic_client_import_error(self):
        """Test Anthropic client when package is not available."""
        with (
            patch.dict("sys.modules", {"anthropic": None}),
            patch(
                "builtins.__import__",
                side_effect=ImportError("No module named 'anthropic'"),
            ),
        ):
            with pytest.raises(PALExecutorError) as exc_info:
                AnthropicClient()
            assert "Anthropic package not installed" in str(exc_info.value)


class TestPromptExecutor:
    """Test PromptExecutor with various scenarios."""

    def test_prompt_executor_initialization(self):
        """Test executor initialization."""
        mock_client = MockLLMClient()
        executor = PromptExecutor(mock_client)

        assert executor.llm_client == mock_client
        assert executor.log_file is None
        assert executor.execution_history == []

    def test_prompt_executor_initialization_with_log_file(self, temp_dir):
        """Test executor initialization with log file."""
        mock_client = MockLLMClient()
        log_file = temp_dir / "test.log"
        executor = PromptExecutor(mock_client, log_file)

        assert executor.log_file == log_file

    @pytest.mark.asyncio
    async def test_execute_with_error_handling(self, sample_prompt_assembly):
        """Test execution with error handling and error result creation."""
        # Create a client that raises an exception
        mock_client = AsyncMock()
        mock_client.generate.side_effect = Exception("Test error")

        executor = PromptExecutor(mock_client)

        with pytest.raises(PALExecutorError) as exc_info:
            await executor.execute("Test prompt", sample_prompt_assembly, "test-model")

        assert "Execution failed for test-prompt" in str(exc_info.value)
        assert len(executor.execution_history) == 1
        error_result = executor.execution_history[0]
        assert not error_result.success
        assert error_result.error == "Test error"

    @pytest.mark.asyncio
    async def test_execute_with_log_file_pre_execution(
        self, sample_prompt_assembly, temp_dir
    ):
        """Test execution logging - pre-execution."""
        mock_client = MockLLMClient("Test response")
        log_file = temp_dir / "test.log"
        executor = PromptExecutor(mock_client, log_file)

        await executor.execute("Test prompt", sample_prompt_assembly, "test-model")

        # Check that log file exists and contains pre-execution data
        assert log_file.exists()
        log_content = log_file.read_text()
        assert "prompt_execution_start" in log_content

    @pytest.mark.asyncio
    async def test_execute_with_log_file_post_execution(
        self, sample_prompt_assembly, temp_dir
    ):
        """Test execution logging - post-execution."""
        mock_client = MockLLMClient("Test response")
        log_file = temp_dir / "test.log"
        executor = PromptExecutor(mock_client, log_file)

        await executor.execute("Test prompt", sample_prompt_assembly, "test-model")

        log_content = log_file.read_text()
        assert "prompt_execution_complete" in log_content

    @pytest.mark.asyncio
    async def test_execute_with_log_file_error(self, sample_prompt_assembly, temp_dir):
        """Test execution logging - error logging."""
        mock_client = AsyncMock()
        mock_client.generate.side_effect = Exception("Test error")

        log_file = temp_dir / "test.log"
        executor = PromptExecutor(mock_client, log_file)

        with pytest.raises(PALExecutorError):
            await executor.execute("Test prompt", sample_prompt_assembly, "test-model")

        log_content = log_file.read_text()
        assert "prompt_execution_error" in log_content
        assert "Test error" in log_content

    @pytest.mark.asyncio
    async def test_log_file_write_failure(self, sample_prompt_assembly, temp_dir):
        """Test handling of log file write failures."""
        mock_client = MockLLMClient("Test response")

        # Use a non-existent directory to cause write failure
        log_file = temp_dir / "nonexistent" / "test.log"
        executor = PromptExecutor(mock_client, log_file)

        # Should not raise exception even if log writing fails
        result = await executor.execute(
            "Test prompt", sample_prompt_assembly, "test-model"
        )
        assert result.success

    def test_estimate_cost_known_models(self):
        """Test cost estimation for known models."""
        mock_client = MockLLMClient()
        executor = PromptExecutor(mock_client)

        # Test OpenAI model
        cost = executor._estimate_cost("gpt-4", 1000, 2000)
        assert cost is not None
        assert cost > 0

        # Test Anthropic model
        cost = executor._estimate_cost("claude-3-sonnet-20240229", 1000, 2000)
        assert cost is not None
        assert cost > 0

    def test_estimate_cost_unknown_model(self):
        """Test cost estimation for unknown models."""
        mock_client = MockLLMClient()
        executor = PromptExecutor(mock_client)

        cost = executor._estimate_cost("unknown-model", 1000, 2000)
        assert cost is None

    def test_estimate_cost_no_tokens(self):
        """Test cost estimation with missing token counts."""
        mock_client = MockLLMClient()
        executor = PromptExecutor(mock_client)

        cost = executor._estimate_cost("gpt-4", None, 2000)
        assert cost is None

        cost = executor._estimate_cost("gpt-4", 1000, None)
        assert cost is None

    def test_estimate_cost_prefix_matching(self):
        """Test cost estimation with model name prefix matching."""
        mock_client = MockLLMClient()
        executor = PromptExecutor(mock_client)

        # Test with full model name that starts with known prefix
        cost = executor._estimate_cost("gpt-4-turbo-preview", 1000, 2000)
        assert cost is not None

        cost = executor._estimate_cost("claude-3-opus-20240229-preview", 1000, 2000)
        assert cost is not None

    def test_get_execution_history(self, sample_prompt_assembly):
        """Test getting execution history."""
        mock_client = MockLLMClient()
        executor = PromptExecutor(mock_client)

        # Initially empty
        history = executor.get_execution_history()
        assert history == []

        # Add some mock history
        from pal.models.schema import ExecutionResult

        result = ExecutionResult(
            prompt_id="test",
            prompt_version="1.0.0",
            model="test-model",
            compiled_prompt="test",
            response="test response",
            metadata={},
            execution_time_ms=100.0,
            timestamp="2024-01-01T00:00:00Z",
        )
        executor.execution_history.append(result)

        history = executor.get_execution_history()
        assert len(history) == 1
        assert history[0] == result

        # Should return a copy, not the original list
        assert history is not executor.execution_history

    def test_clear_history(self):
        """Test clearing execution history."""
        mock_client = MockLLMClient()
        executor = PromptExecutor(mock_client)

        # Add some mock history
        from pal.models.schema import ExecutionResult

        result = ExecutionResult(
            prompt_id="test",
            prompt_version="1.0.0",
            model="test-model",
            compiled_prompt="test",
            response="test response",
            metadata={},
            execution_time_ms=100.0,
            timestamp="2024-01-01T00:00:00Z",
        )
        executor.execution_history.append(result)
        assert len(executor.execution_history) == 1

        executor.clear_history()
        assert len(executor.execution_history) == 0

    @pytest.mark.asyncio
    async def test_execute_with_custom_kwargs(self, sample_prompt_assembly):
        """Test execution with custom kwargs passed to LLM client."""
        mock_client = AsyncMock()
        mock_client.generate.return_value = {
            "response": "Test response",
            "input_tokens": 10,
            "output_tokens": 20,
            "finish_reason": "stop",
        }

        executor = PromptExecutor(mock_client)

        await executor.execute(
            "Test prompt",
            sample_prompt_assembly,
            "test-model",
            temperature=0.3,
            max_tokens=1000,
            top_p=0.9,
            custom_param="test",
        )

        # Verify kwargs were passed to client
        mock_client.generate.assert_called_once_with(
            "Test prompt", "test-model", 0.3, 1000, top_p=0.9, custom_param="test"
        )

    @patch("pal.core.executor.asyncio.to_thread")
    @pytest.mark.asyncio
    async def test_write_to_log_file_exception_handling(
        self, mock_to_thread, sample_prompt_assembly, temp_dir
    ):
        """Test log file writing with exception handling."""
        mock_client = MockLLMClient("Test response")
        log_file = temp_dir / "test.log"
        executor = PromptExecutor(mock_client, log_file)

        # Make asyncio.to_thread raise an exception
        mock_to_thread.side_effect = Exception("Thread error")

        # Should not raise exception even if thread writing fails
        result = await executor.execute(
            "Test prompt", sample_prompt_assembly, "test-model"
        )
        assert result.success

    @pytest.mark.asyncio
    async def test_append_to_file_functionality(self, sample_prompt_assembly, temp_dir):
        """Test the _append_to_file method functionality."""
        mock_client = MockLLMClient("Test response")
        log_file = temp_dir / "test.log"
        executor = PromptExecutor(mock_client, log_file)

        # Test the append functionality directly
        executor._append_to_file("test content\n")
        assert log_file.exists()
        content = log_file.read_text()
        assert "test content" in content

        # Test appending more content
        executor._append_to_file("more content\n")
        content = log_file.read_text()
        assert "test content" in content
        assert "more content" in content

    @pytest.mark.asyncio
    async def test_append_to_file_no_log_file(self):
        """Test _append_to_file when no log file is set."""
        mock_client = MockLLMClient("Test response")
        executor = PromptExecutor(mock_client)  # No log file

        # Should not raise exception
        executor._append_to_file("test content\n")


class TestMockLLMClientEdgeCases:
    """Test MockLLMClient edge cases for complete coverage."""

    @pytest.mark.asyncio
    async def test_mock_client_token_calculation(self):
        """Test MockLLMClient token calculation with various inputs."""
        client = MockLLMClient("Short")
        result = await client.generate("Very long prompt with many words", "test-model")

        # Should calculate tokens based on word count
        assert result["input_tokens"] > 0
        assert result["output_tokens"] > 0

        # Test with empty strings
        client = MockLLMClient("")
        result = await client.generate("", "test-model")

        # Should still return some values
        assert "input_tokens" in result
        assert "output_tokens" in result

    @pytest.mark.asyncio
    async def test_mock_client_parameter_tracking(self):
        """Test MockLLMClient parameter tracking."""
        client = MockLLMClient("Test response")

        await client.generate(
            "Test prompt",
            "test-model",
            temperature=0.8,
            max_tokens=500,
            custom_param="value",
        )

        assert client.call_count == 1
        assert client.last_prompt == "Test prompt"
        assert client.last_model == "test-model"

        # Call again to test increment
        await client.generate("Second prompt", "another-model")

        assert client.call_count == 2
        assert client.last_prompt == "Second prompt"
        assert client.last_model == "another-model"
