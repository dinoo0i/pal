"""Pydantic models for PAL schema validation."""

from __future__ import annotations

from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Literal, Union
from urllib.parse import urlparse

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)


class ComponentType(str, Enum):
    """Valid component types in PAL libraries."""

    PERSONA = "persona"
    TASK = "task"
    CONTEXT = "context"
    RULES = "rules"
    EXAMPLES = "examples"
    OUTPUT_SCHEMA = "output_schema"
    REASONING = "reasoning"
    TRAIT = "trait"
    NOTE = "note"


class VariableType(str, Enum):
    """Valid variable types in PAL."""

    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    LIST = "list"
    DICT = "dict"
    ANY = "any"


class PALVariable(BaseModel):
    """Model for PAL variable definitions."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(..., pattern=r"^[a-zA-Z_][a-zA-Z0-9_]*$")
    type: VariableType
    description: str
    required: bool = True
    default: Any = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate variable name follows Python identifier rules."""
        if not v.isidentifier():
            raise ValueError(f"Variable name '{v}' is not a valid identifier")
        return v


class PALComponent(BaseModel):
    """Model for PAL component definitions."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(..., pattern=r"^[a-zA-Z_][a-zA-Z0-9_]*$")
    description: str
    content: str
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate component name follows Python identifier rules."""
        if not v.isidentifier():
            raise ValueError(f"Component name '{v}' is not a valid identifier")
        return v


class ComponentLibrary(BaseModel):
    """Model for PAL component library files (.pal.lib)."""

    model_config = ConfigDict(extra="forbid")

    pal_version: Literal["1.0"] = "1.0"
    library_id: str = Field(..., pattern=r"^[a-zA-Z0-9._-]+$")
    version: str = Field(..., pattern=r"^\d+\.\d+\.\d+$")
    description: str
    type: ComponentType
    components: List[PALComponent]
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("components")
    @classmethod
    def validate_unique_component_names(
        cls, v: List[PALComponent]
    ) -> List[PALComponent]:
        """Ensure component names are unique within the library."""
        names = [comp.name for comp in v]
        if len(names) != len(set(names)):
            duplicates = [name for name in names if names.count(name) > 1]
            raise ValueError(f"Duplicate component names found: {duplicates}")
        return v


class PromptAssembly(BaseModel):
    """Model for PAL prompt assembly files (.pal)."""

    model_config = ConfigDict(extra="forbid")

    pal_version: Literal["1.0"] = "1.0"
    id: str = Field(..., pattern=r"^[a-zA-Z0-9_-]+$")
    version: str = Field(..., pattern=r"^\d+\.\d+\.\d+$")
    description: str
    author: str | None = None
    imports: Dict[str, Union[str, Path]] = Field(default_factory=dict)
    variables: List[PALVariable] = Field(default_factory=list)
    composition: List[str]
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("imports")
    @classmethod
    def validate_imports(
        cls, v: Dict[str, Union[str, Path]]
    ) -> Dict[str, Union[str, Path]]:
        """Validate import paths and URLs."""
        for alias, path_or_url in v.items():
            if not alias.isidentifier():
                raise ValueError(f"Import alias '{alias}' is not a valid identifier")

            path_str = str(path_or_url)

            # Check if it's a URL
            parsed = urlparse(path_str)
            if parsed.scheme in ("http", "https"):
                continue

            # Check if it's a file path
            if not path_str.endswith((".pal.lib", ".pal")):
                raise ValueError(
                    f"Import path '{path_str}' must end with .pal.lib or .pal"
                )

        return v

    @field_validator("variables")
    @classmethod
    def validate_unique_variable_names(cls, v: List[PALVariable]) -> List[PALVariable]:
        """Ensure variable names are unique within the assembly."""
        names = [var.name for var in v]
        if len(names) != len(set(names)):
            duplicates = [name for name in names if names.count(name) > 1]
            raise ValueError(f"Duplicate variable names found: {duplicates}")
        return v

    @field_validator("composition")
    @classmethod
    def validate_composition_not_empty(cls, v: List[str]) -> List[str]:
        """Ensure composition is not empty."""
        if not v:
            raise ValueError("Composition cannot be empty")
        return v


class EvaluationAssertion(BaseModel):
    """Model for evaluation assertions in .eval.yaml files."""

    model_config = ConfigDict(extra="forbid")

    type: str
    name: str | None = None
    description: str | None = None
    config: Dict[str, Any] = Field(default_factory=dict)


class EvaluationTestCase(BaseModel):
    """Model for evaluation test cases."""

    model_config = ConfigDict(extra="forbid")

    name: str
    description: str | None = None
    variables: Dict[str, Any]
    assertions: List[EvaluationAssertion]
    metadata: Dict[str, Any] = Field(default_factory=dict)


class EvaluationSuite(BaseModel):
    """Model for PAL evaluation files (.eval.yaml)."""

    model_config = ConfigDict(extra="forbid")

    pal_version: Literal["1.0"] = "1.0"
    prompt_id: str
    target_version: str = Field(pattern=r"^\d+\.\d+\.\d+$")
    description: str | None = None
    test_cases: List[EvaluationTestCase]
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("test_cases")
    @classmethod
    def validate_unique_test_names(
        cls, v: List[EvaluationTestCase]
    ) -> List[EvaluationTestCase]:
        """Ensure test case names are unique within the suite."""
        names = [test.name for test in v]
        if len(names) != len(set(names)):
            duplicates = [name for name in names if names.count(name) > 1]
            raise ValueError(f"Duplicate test case names found: {duplicates}")
        return v


class ExecutionResult(BaseModel):
    """Model for prompt execution results."""

    model_config = ConfigDict(extra="forbid")

    prompt_id: str
    prompt_version: str
    model: str
    compiled_prompt: str
    response: str
    metadata: Dict[str, Any]
    execution_time_ms: float
    input_tokens: int | None = None
    output_tokens: int | None = None
    cost_usd: float | None = None
    timestamp: str
    success: bool = True
    error: str | None = None
