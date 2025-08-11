"""Core PAL exceptions."""

from typing import Any


class PALError(Exception):
    """Base exception for all PAL errors."""

    def __init__(self, message: str, context: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.context = context or {}


class PALValidationError(PALError):
    """Raised when PAL file validation fails."""

    pass


class PALLoadError(PALError):
    """Raised when loading PAL files fails."""

    pass


class PALResolverError(PALError):
    """Raised when resolving dependencies fails."""

    pass


class PALCompilerError(PALError):
    """Raised when compiling prompts fails."""

    pass


class PALExecutorError(PALError):
    """Raised when executing prompts fails."""

    pass


class PALCircularDependencyError(PALResolverError):
    """Raised when circular dependencies are detected."""

    pass


class PALMissingVariableError(PALCompilerError):
    """Raised when required variables are missing during compilation."""

    pass


class PALMissingComponentError(PALCompilerError):
    """Raised when referenced components are missing."""

    pass
