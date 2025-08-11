"""
Prompt Assembly Language (PAL) - A framework for managing LLM prompts as versioned, composable software artifacts.
"""

__version__ = "0.1.0"
__author__ = "Nicolas Iglesias"
__email__ = "nfiglesias@gmail.com"

from .core.compiler import PromptCompiler
from .core.evaluation import EvaluationReporter, EvaluationRunner
from .core.executor import AnthropicClient, MockLLMClient, OpenAIClient, PromptExecutor
from .core.loader import Loader
from .core.resolver import Resolver
from .exceptions.core import (
    PALCircularDependencyError,
    PALCompilerError,
    PALError,
    PALExecutorError,
    PALLoadError,
    PALMissingComponentError,
    PALMissingVariableError,
    PALResolverError,
    PALValidationError,
)
from .models.schema import (
    ComponentLibrary,
    EvaluationSuite,
    ExecutionResult,
    PromptAssembly,
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
    "PALMissingVariableError",
    "PALMissingComponentError",
    "PALCircularDependencyError",
]
