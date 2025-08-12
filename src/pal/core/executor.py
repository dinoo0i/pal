"""PAL prompt execution with LLM integration and observability."""

from __future__ import annotations

import asyncio
import json
import time
from abc import ABC, abstractmethod
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Protocol
from uuid import uuid4

import structlog

from ..exceptions.core import PALExecutorError
from ..models.schema import ExecutionResult, PromptAssembly

logger = structlog.get_logger()


class LLMClient(Protocol):
    """Protocol for LLM clients."""

    async def generate(
        self,
        prompt: str,
        model: str,
        temperature: float = 0.7,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Generate a response from the LLM."""
        ...


class BaseLLMClient(ABC):
    """Base class for LLM clients."""

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        model: str,
        temperature: float = 0.7,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Generate a response from the LLM."""


class MockLLMClient(BaseLLMClient):
    """Mock LLM client for testing and development.

    Provides a mock implementation of the LLM client interface for testing
    PAL prompts without making actual API calls. Useful for unit tests and
    local development.

    Attributes:
        response: The mock response to return
        call_count: Number of times generate() has been called
        last_prompt: The last prompt passed to generate()
        last_model: The last model name passed to generate()

    Example:
        >>> mock_client = MockLLMClient(response="Test response")
        >>> executor = PromptExecutor(mock_client)
        >>> result = await executor.execute(assembly, variables)
    """

    def __init__(self, response: str = "Mock response") -> None:
        """Initialize the mock client.

        Args:
            response: The mock response string to return from generate()
        """
        self.response = response
        self.call_count = 0
        self.last_prompt = ""
        self.last_model = ""

    async def generate(
        self,
        prompt: str,
        model: str,
        temperature: float = 0.7,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Generate a mock response."""
        self.call_count += 1
        self.last_prompt = prompt
        self.last_model = model

        # Simulate some processing time
        await asyncio.sleep(0.1)

        return {
            "response": self.response,
            "input_tokens": int(len(prompt.split()) * 1.3),  # Rough estimate
            "output_tokens": int(len(self.response.split()) * 1.3),
            "model": model,
            "finish_reason": "stop",
        }


class OpenAIClient(BaseLLMClient):
    """OpenAI API client for GPT model integration.

    Implements the LLM client interface for OpenAI's GPT models. Requires
    the 'openai' package to be installed.

    Note:
        Install with: pip install openai

    Example:
        >>> client = OpenAIClient(api_key="sk-...")
        >>> executor = PromptExecutor(client)
        >>> result = await executor.execute(
        ...     assembly,
        ...     variables={"topic": "Python"},
        ...     model="gpt-4",
        ...     temperature=0.7
        ... )
    """

    def __init__(self, api_key: str | None = None) -> None:
        """Initialize the OpenAI client.

        Args:
            api_key: OpenAI API key. If not provided, will use OPENAI_API_KEY env var.

        Raises:
            PALExecutorError: If the openai package is not installed
        """
        try:
            import openai

            self.client = openai.AsyncOpenAI(api_key=api_key)
        except ImportError as e:
            raise PALExecutorError(
                "OpenAI package not installed. Install with: pip install openai",
                context={"client_type": "OpenAI"},
            ) from e

    async def generate(
        self,
        prompt: str,
        model: str,
        temperature: float = 0.7,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Generate response using OpenAI API."""
        try:
            response = await self.client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs,
            )

            choice = response.choices[0]
            return {
                "response": choice.message.content or "",
                "input_tokens": response.usage.prompt_tokens
                if response.usage
                else None,
                "output_tokens": response.usage.completion_tokens
                if response.usage
                else None,
                "model": response.model,
                "finish_reason": choice.finish_reason,
            }
        except Exception as e:
            raise PALExecutorError(
                f"OpenAI API error: {e}", context={"model": model, "error": str(e)}
            ) from e


class AnthropicClient(BaseLLMClient):
    """Anthropic API client for Claude model integration.

    Implements the LLM client interface for Anthropic's Claude models. Requires
    the 'anthropic' package to be installed.

    Note:
        Install with: pip install anthropic

    Example:
        >>> client = AnthropicClient(api_key="sk-ant-...")
        >>> executor = PromptExecutor(client)
        >>> result = await executor.execute(
        ...     assembly,
        ...     variables={"code": "def hello(): pass"},
        ...     model="claude-3-opus-20240229",
        ...     max_tokens=1000
        ... )
    """

    def __init__(self, api_key: str | None = None) -> None:
        """Initialize the Anthropic client.

        Args:
            api_key: Anthropic API key. If not provided, will use ANTHROPIC_API_KEY env var.

        Raises:
            PALExecutorError: If the anthropic package is not installed
        """
        try:
            import anthropic

            self.client = anthropic.AsyncAnthropic(api_key=api_key)
        except ImportError as e:
            raise PALExecutorError(
                "Anthropic package not installed. Install with: pip install anthropic",
                context={"client_type": "Anthropic"},
            ) from e

    async def generate(
        self,
        prompt: str,
        model: str,
        temperature: float = 0.7,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Generate response using Anthropic API."""
        try:
            response = await self.client.messages.create(
                model=model,
                max_tokens=max_tokens or 1024,
                temperature=temperature,
                messages=[{"role": "user", "content": prompt}],
                **kwargs,
            )

            return {
                "response": response.content[0].text if response.content else "",
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens,
                "model": response.model,
                "finish_reason": response.stop_reason,
            }
        except Exception as e:
            raise PALExecutorError(
                f"Anthropic API error: {e}", context={"model": model, "error": str(e)}
            ) from e


class PromptExecutor:
    """Executes compiled prompts with LLM clients and provides observability.

    The PromptExecutor handles the execution of compiled PAL prompts through
    various LLM providers. It provides:

    - Unified interface for different LLM providers (OpenAI, Anthropic, etc.)
    - Execution tracking and history management
    - Structured logging and observability
    - Error handling and retry logic

    Attributes:
        llm_client: The LLM client instance for API calls
        log_file: Optional path for execution logging
        execution_history: List of all execution results

    Example:
        >>> from pal import AnthropicClient, PromptExecutor, PromptCompiler
        >>> client = AnthropicClient(api_key="...")
        >>> executor = PromptExecutor(client)
        >>> compiler = PromptCompiler()
        >>>
        >>> compiled = await compiler.compile_from_file(Path("prompt.pal"))
        >>> result = await executor.execute(
        ...     compiled_prompt=compiled,
        ...     prompt_assembly=assembly,
        ...     model="claude-3-opus-20240229",
        ...     temperature=0.7
        ... )
    """

    def __init__(
        self, llm_client: LLMClient | BaseLLMClient, log_file: Path | None = None
    ) -> None:
        """Initialize the executor.

        Args:
            llm_client: An LLM client instance (OpenAIClient, AnthropicClient, etc.)
            log_file: Optional path to write execution logs in JSON format
        """
        self.llm_client = llm_client
        self.log_file = log_file
        self.execution_history: list[ExecutionResult] = []

    async def execute(
        self,
        compiled_prompt: str,
        prompt_assembly: PromptAssembly,
        model: str,
        temperature: float = 0.7,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> ExecutionResult:
        """Execute a compiled prompt and return structured results.

        Args:
            compiled_prompt: The compiled prompt string from PromptCompiler
            prompt_assembly: The original PromptAssembly object
            model: Model identifier (e.g., "gpt-4", "claude-3-opus-20240229")
            temperature: Sampling temperature (0.0 to 1.0)
            max_tokens: Maximum tokens to generate
            **kwargs: Additional model-specific parameters

        Returns:
            ExecutionResult containing the response and metadata

        Raises:
            PALExecutorError: If the LLM API call fails

        Example:
            >>> result = await executor.execute(
            ...     compiled_prompt="Analyze this code...",
            ...     prompt_assembly=assembly,
            ...     model="gpt-4",
            ...     temperature=0.3,
            ...     max_tokens=2000
            ... )
            >>> print(result.response)
        """
        execution_id = str(uuid4())
        start_time = time.time()
        timestamp = datetime.now(UTC).isoformat()

        # Pre-execution logging
        await self._log_pre_execution(
            execution_id,
            prompt_assembly,
            model,
            compiled_prompt,
            temperature,
            max_tokens,
            kwargs,
        )

        try:
            # Execute the prompt
            response_data = await self.llm_client.generate(
                compiled_prompt, model, temperature, max_tokens, **kwargs
            )

            execution_time = (
                time.time() - start_time
            ) * 1000  # Convert to milliseconds

            # Create execution result
            result = ExecutionResult(
                prompt_id=prompt_assembly.id,
                prompt_version=prompt_assembly.version,
                model=model,
                compiled_prompt=compiled_prompt,
                response=response_data.get("response", ""),
                metadata={
                    "execution_id": execution_id,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                    "finish_reason": response_data.get("finish_reason"),
                    **kwargs,
                },
                execution_time_ms=execution_time,
                input_tokens=response_data.get("input_tokens"),
                output_tokens=response_data.get("output_tokens"),
                cost_usd=self._estimate_cost(
                    model,
                    response_data.get("input_tokens"),
                    response_data.get("output_tokens"),
                ),
                timestamp=timestamp,
                success=True,
            )

            # Post-execution logging
            await self._log_post_execution(result)

            # Store in history
            self.execution_history.append(result)

            return result

        except Exception as e:
            execution_time = (time.time() - start_time) * 1000

            # Create error result
            error_result = ExecutionResult(
                prompt_id=prompt_assembly.id,
                prompt_version=prompt_assembly.version,
                model=model,
                compiled_prompt=compiled_prompt,
                response="",
                metadata={
                    "execution_id": execution_id,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                    **kwargs,
                },
                execution_time_ms=execution_time,
                timestamp=timestamp,
                success=False,
                error=str(e),
            )

            # Log the error
            await self._log_error(error_result, e)

            # Store in history
            self.execution_history.append(error_result)

            raise PALExecutorError(
                f"Execution failed for {prompt_assembly.id}: {e}",
                context={
                    "execution_id": execution_id,
                    "prompt_id": prompt_assembly.id,
                    "model": model,
                    "error": str(e),
                },
            ) from e

    async def _log_pre_execution(
        self,
        execution_id: str,
        prompt_assembly: PromptAssembly,
        model: str,
        compiled_prompt: str,
        temperature: float,
        max_tokens: int | None,
        kwargs: dict[str, Any],
    ) -> None:
        """Log pre-execution information."""
        log_data = {
            "execution_id": execution_id,
            "prompt_id": prompt_assembly.id,
            "prompt_version": prompt_assembly.version,
            "model": model,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "compiled_prompt_length": len(compiled_prompt),
            "timestamp": datetime.now(UTC).isoformat(),
        }

        logger.info("Starting prompt execution", **log_data)

        if self.log_file:
            log_data["event"] = "prompt_execution_start"
            await self._write_to_log_file(log_data)

    async def _log_post_execution(self, result: ExecutionResult) -> None:
        """Log post-execution information."""
        log_data = {
            "execution_id": result.metadata.get("execution_id"),
            "prompt_id": result.prompt_id,
            "prompt_version": result.prompt_version,
            "model": result.model,
            "success": result.success,
            "execution_time_ms": result.execution_time_ms,
            "input_tokens": result.input_tokens,
            "output_tokens": result.output_tokens,
            "cost_usd": result.cost_usd,
            "response_length": len(result.response),
            "timestamp": result.timestamp,
        }

        logger.info("Prompt execution completed", **log_data)

        if self.log_file:
            log_data["event"] = "prompt_execution_complete"
            await self._write_to_log_file(log_data)

    async def _log_error(self, result: ExecutionResult, error: Exception) -> None:
        """Log execution errors."""
        log_data = {
            "execution_id": result.metadata.get("execution_id"),
            "prompt_id": result.prompt_id,
            "model": result.model,
            "error": str(error),
            "error_type": type(error).__name__,
            "execution_time_ms": result.execution_time_ms,
            "timestamp": result.timestamp,
        }

        logger.error("Prompt execution failed", **log_data)

        if self.log_file:
            log_data["event"] = "prompt_execution_error"
            await self._write_to_log_file(log_data)

    async def _write_to_log_file(self, data: dict[str, Any]) -> None:
        """Write log data to file."""
        if not self.log_file:
            return

        try:
            import asyncio

            log_line = json.dumps(data, default=str) + "\n"
            await asyncio.to_thread(self._append_to_file, log_line)
        except Exception as e:
            logger.warning("Failed to write to log file", error=str(e))

    def _append_to_file(self, content: str) -> None:
        """Append content to log file (thread-safe)."""
        if self.log_file:
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(content)

    def _estimate_cost(
        self, model: str, input_tokens: int | None, output_tokens: int | None
    ) -> float | None:
        """Estimate cost based on token counts (rough estimates)."""
        if not input_tokens or not output_tokens:
            return None

        # Rough cost estimates per 1K tokens (as of 2024)
        cost_table = {
            # OpenAI models
            "gpt-4": {"input": 0.03, "output": 0.06},
            "gpt-4-turbo": {"input": 0.01, "output": 0.03},
            "gpt-3.5-turbo": {"input": 0.0015, "output": 0.002},
            # Anthropic models
            "claude-3-opus-20240229": {"input": 0.015, "output": 0.075},
            "claude-3-sonnet-20240229": {"input": 0.003, "output": 0.015},
            "claude-3-haiku-20240307": {"input": 0.00025, "output": 0.00125},
        }

        # Find matching model (prefix matching)
        model_costs = None
        for model_key, costs in cost_table.items():
            if model.startswith(model_key):
                model_costs = costs
                break

        if not model_costs:
            return None  # Unknown model

        input_cost = (input_tokens / 1000) * model_costs["input"]
        output_cost = (output_tokens / 1000) * model_costs["output"]

        return input_cost + output_cost

    def get_execution_history(self) -> list[ExecutionResult]:
        """Get the execution history."""
        return self.execution_history.copy()

    def clear_history(self) -> None:
        """Clear the execution history."""
        self.execution_history.clear()
