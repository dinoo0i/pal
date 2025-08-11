"""
Prompt Assembly Language (PAL) - A framework for managing LLM prompts as versioned, composable software artifacts.
"""

__version__ = "0.1.0"
__author__ = "Nicolas Iglesias"
__email__ = "nfiglesias@gmail.com"

from .core.compiler import PromptCompiler
from .core.evaluation import EvaluationRunner, EvaluationReporter
from .core.executor import PromptExecutor, MockLLMClient, OpenAIClient, AnthropicClient
from .core.loader import Loader
from .core.resolver import Resolver
from .exceptions.core import (
    PALError,
    PALValidationError,
    PALLoadError,
    PALResolverError,
    PALCompilerError,
    PALExecutorError,
)
from .models.schema import (
    PromptAssembly,
    ComponentLibrary,
    EvaluationSuite,
    ExecutionResult,
)

__all__ = [
    # Core classes
    "PromptCompiler",
    "PromptExecutor",
    "Loader",
    "Resolver",
    "EvaluationRunner",
    "EvaluationReporter",
    # LLM Clients
    "MockLLMClient",
    "OpenAIClient",
    "AnthropicClient",
    # Data models
    "PromptAssembly",
    "ComponentLibrary",
    "EvaluationSuite",
    "ExecutionResult",
    # Exceptions
    "PALError",
    "PALValidationError",
    "PALLoadError",
    "PALResolverError",
    "PALCompilerError",
    "PALExecutorError",
]
