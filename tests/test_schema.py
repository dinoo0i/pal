"""Tests for PAL schema validation and Pydantic models."""

import pytest
from pydantic import ValidationError

from pal.models.schema import (
    ComponentLibrary,
    PromptAssembly,
    PALVariable,
    VariableType,
    PALComponent,
    ComponentType,
    ExecutionResult,
    EvaluationSuite,
    EvaluationTestCase,
    EvaluationAssertion,
)


class TestPALVariable:
    """Test variable definition validation."""

    def test_valid_variable_definition(self):
        """Test creating valid variable definitions."""
        var = PALVariable(
            name="test_var",
            type=VariableType.STRING,
            description="A test variable",
            required=True,
        )
        assert var.name == "test_var"
        assert var.type == VariableType.STRING
        assert var.required is True
        assert var.default is None

    def test_variable_with_default(self):
        """Test variable with default value."""
        var = PALVariable(
            name="optional_var",
            type=VariableType.INTEGER,
            description="An optional variable",
            required=False,
            default=42,
        )
        assert var.default == 42
        assert var.required is False

    def test_invalid_variable_name(self):
        """Test validation of variable names."""
        with pytest.raises(ValidationError):
            PALVariable(
                name="",  # Empty name should fail
                type=VariableType.STRING,
                description="Test",
            )

    def test_all_variable_types(self):
        """Test all supported variable types."""
        types = [
            VariableType.STRING,
            VariableType.INTEGER,
            VariableType.FLOAT,
            VariableType.BOOLEAN,
            VariableType.LIST,
            VariableType.DICT,
            VariableType.ANY,
        ]

        for var_type in types:
            var = PALVariable(
                name=f"var_{var_type.value}",
                type=var_type,
                description=f"Variable of type {var_type.value}",
            )
            assert var.type == var_type


class TestPALComponent:
    """Test component validation."""

    def test_valid_component(self):
        """Test creating a valid component."""
        comp = PALComponent(
            name="test_component",
            description="A test component",
            content="You are a helpful assistant.",
        )
        assert comp.name == "test_component"
        assert "helpful assistant" in comp.content

    def test_component_name_validation(self):
        """Test component name validation."""
        # Valid names
        valid_names = ["component", "test_component", "component123", "Component_Name"]
        for name in valid_names:
            comp = PALComponent(name=name, description="Test", content="Content")
            assert comp.name == name

        # Invalid names (empty)
        with pytest.raises(ValidationError):
            PALComponent(name="", description="Test", content="Content")


class TestComponentLibrary:
    """Test component library validation."""

    def test_valid_library(self):
        """Test creating a valid component library."""
        components = [
            PALComponent(name="comp1", description="First", content="Content 1"),
            PALComponent(name="comp2", description="Second", content="Content 2"),
        ]

        lib = ComponentLibrary(
            pal_version="1.0",
            library_id="test.library",
            version="1.0.0",
            description="Test library",
            type=ComponentType.TRAIT,
            components=components,
        )

        assert lib.library_id == "test.library"
        assert len(lib.components) == 2
        assert lib.type == ComponentType.TRAIT

    def test_duplicate_component_names(self):
        """Test that duplicate component names are properly rejected."""
        components = [
            PALComponent(name="duplicate", description="First", content="Content 1"),
            PALComponent(name="duplicate", description="Second", content="Content 2"),
        ]

        # The schema should reject duplicate component names
        with pytest.raises(ValidationError) as exc_info:
            ComponentLibrary(
                pal_version="1.0",
                library_id="test.library",
                version="1.0.0",
                description="Test library",
                type=ComponentType.TRAIT,
                components=components,
            )

        assert "Duplicate component names" in str(exc_info.value)

    def test_library_types(self):
        """Test all library types."""
        for lib_type in ComponentType:
            lib = ComponentLibrary(
                pal_version="1.0",
                library_id="test.library",
                version="1.0.0",
                description="Test library",
                type=lib_type,
                components=[],
            )
            assert lib.type == lib_type


class TestPromptAssembly:
    """Test prompt assembly validation."""

    def test_valid_assembly(self):
        """Test creating a valid prompt assembly."""
        variables = [
            PALVariable(
                name="user_input", type=VariableType.STRING, description="User input"
            )
        ]

        assembly = PromptAssembly(
            pal_version="1.0",
            id="test-prompt",
            version="1.0.0",
            description="Test prompt",
            author="Test Author",
            imports={"lib1": "path/to/lib1.pal.lib"},
            variables=variables,
            composition=["{{ user_input }}", "Please respond."],
        )

        assert assembly.id == "test-prompt"
        assert len(assembly.variables) == 1
        assert len(assembly.imports) == 1
        assert len(assembly.composition) == 2

    def test_minimal_assembly(self):
        """Test assembly with minimal required fields."""
        assembly = PromptAssembly(
            pal_version="1.0",
            id="minimal-prompt",
            version="1.0.0",
            description="Minimal prompt",
            composition=["Hello, world!"],
        )

        assert assembly.id == "minimal-prompt"
        assert len(assembly.variables) == 0
        assert len(assembly.imports) == 0
        assert assembly.author is None

    def test_empty_composition_validation(self):
        """Test that empty composition is invalid."""
        with pytest.raises(ValidationError):
            PromptAssembly(
                pal_version="1.0",
                id="empty-prompt",
                version="1.0.0",
                description="Empty prompt",
                composition=[],  # Should not be empty
            )


class TestExecutionResult:
    """Test execution result model."""

    def test_valid_execution_result(self):
        """Test creating a valid execution result."""
        result = ExecutionResult(
            prompt_id="test-prompt",
            prompt_version="1.0.0",
            model="gpt-4",
            compiled_prompt="Test prompt",
            response="Generated response",
            metadata={"key": "value"},
            execution_time_ms=1500.5,
            input_tokens=100,
            output_tokens=50,
            timestamp="2024-01-01T00:00:00Z",
            success=True,
        )

        assert result.success is True
        assert result.response == "Generated response"
        assert result.input_tokens == 100
        assert result.execution_time_ms == 1500.5

    def test_failed_execution_result(self):
        """Test creating a failed execution result."""
        result = ExecutionResult(
            prompt_id="failed-prompt",
            prompt_version="1.0.0",
            model="gpt-4",
            compiled_prompt="Test prompt",
            response="",
            metadata={},
            execution_time_ms=100.0,
            input_tokens=0,
            output_tokens=0,
            timestamp="2024-01-01T00:00:00Z",
            success=False,
            error="API timeout",
        )

        assert result.success is False
        assert result.error == "API timeout"


class TestEvaluationModels:
    """Test evaluation-related models."""

    def test_assertion_types(self):
        """Test assertion creation."""
        assertion = EvaluationAssertion(type="json_valid", config={})
        assert assertion.type == "json_valid"

    def test_test_case(self):
        """Test creating a test case."""
        assertions = [
            EvaluationAssertion(type="json_valid", config={}),
            EvaluationAssertion(
                type="contains", config={"text": "expected", "case_sensitive": True}
            ),
        ]

        test_case = EvaluationTestCase(
            name="test_case_1",
            description="A test case",
            variables={"input": "test"},
            assertions=assertions,
        )

        assert test_case.name == "test_case_1"
        assert len(test_case.assertions) == 2
        assert test_case.variables["input"] == "test"

    def test_evaluation_suite(self):
        """Test creating an evaluation suite."""
        test_cases = [
            EvaluationTestCase(
                name="test1",
                description="First test",
                variables={},
                assertions=[EvaluationAssertion(type="json_valid", config={})],
            ),
            EvaluationTestCase(
                name="test2",
                description="Second test",
                variables={"var": "value"},
                assertions=[
                    EvaluationAssertion(type="length", config={"min_length": 10})
                ],
            ),
        ]

        suite = EvaluationSuite(
            pal_version="1.0",
            prompt_id="test-prompt",
            target_version="1.0.0",
            description="Test suite",
            test_cases=test_cases,
        )

        assert suite.prompt_id == "test-prompt"
        assert len(suite.test_cases) == 2
        assert suite.test_cases[0].name == "test1"
