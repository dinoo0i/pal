"""Core PAL exceptions."""

from typing import Any


class PALError(Exception):
    """Base exception for all PAL errors."""

    def __init__(self, message: str, context: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.context = context or {}


class PALValidationError(PALError):
    """Raised when PAL file validation fails."""


class PALLoadError(PALError):
    """Raised when loading PAL files fails."""


class PALResolverError(PALError):
    """Raised when resolving dependencies fails."""


class PALCompilerError(PALError):
    """Raised when compiling prompts fails."""


class PALExecutorError(PALError):
    """Raised when executing prompts fails."""


class PALCircularDependencyError(PALResolverError):
    """Raised when circular dependencies are detected."""


class PALMissingVariableError(PALCompilerError):
    """Raised when required variables are missing during compilation."""


class PALMissingComponentError(PALCompilerError):
    """Raised when referenced components are missing."""
