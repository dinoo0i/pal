"""Tests for PAL error handling and exception scenarios."""

import tempfile
from pathlib import Path
from unittest.mock import Mock

import pytest
import yaml

from pal.core.compiler import PromptCompiler
from pal.core.executor import PromptExecutor
from pal.core.loader import Loader
from pal.core.resolver import Resolver
from pal.exceptions.core import (
    PALCircularDependencyError,
    PALCompilerError,
    PALError,
    PALExecutorError,
    PALMissingComponentError,
    PALMissingVariableError,
    PALResolverError,
    PALValidationError,
)
from pal.models.schema import (
    PALVariable,
    PromptAssembly,
    VariableType,
)


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


class TestPALExceptionHierarchy:
    """Test PAL exception class hierarchy and properties."""

    def test_pal_error_base_class(self):
        """Test PALError base class functionality."""
        error = PALError("Test error message")
        assert str(error) == "Test error message"
        assert error.context == {}  # Default is empty dict, not None

        # Test with context
        context = {"key": "value", "details": "additional info"}
        error_with_context = PALError("Test error with context", context)
        assert error_with_context.context == context

    def test_validation_error(self):
        """Test PALValidationError."""
        error = PALValidationError("Invalid PAL file format")
        assert isinstance(error, PALError)
        assert "Invalid PAL file format" in str(error)

    def test_compiler_error(self):
        """Test PALCompilerError."""
        context = {"template": "{{ invalid }}", "line": 5}
        error = PALCompilerError("Template compilation failed", context)
        assert isinstance(error, PALError)
        assert error.context == context

    def test_missing_variable_error(self):
        """Test PALMissingVariableError."""
        missing_vars = ["var1", "var2"]
        context = {"missing_variables": missing_vars}
        error = PALMissingVariableError("Missing required variables", context)
        assert isinstance(error, PALError)
        assert error.context["missing_variables"] == missing_vars

    def test_missing_component_error(self):
        """Test PALMissingComponentError."""
        error = PALMissingComponentError("Component not found")
        assert isinstance(error, PALError)

    def test_resolver_error(self):
        """Test PALResolverError."""
        error = PALResolverError("Failed to resolve dependency")
        assert isinstance(error, PALError)

    def test_circular_dependency_error(self):
        """Test PALCircularDependencyError."""
        cycle = ["A", "B", "C", "A"]
        context = {"cycle": cycle}
        error = PALCircularDependencyError("Circular dependency detected", context)
        assert isinstance(error, PALResolverError)
        assert error.context["cycle"] == cycle

    def test_execution_error(self):
        """Test PALExecutorError."""
        error = PALExecutorError("LLM execution failed")
        assert isinstance(error, PALError)


class TestLoaderExceptions:
    """Test exception handling in the Loader class."""

    def test_load_nonexistent_file(self):
        """Test loading a file that doesn't exist."""
        loader = Loader()
        nonexistent_path = Path("/nonexistent/path/file.pal")

        with pytest.raises(
            Exception
        ) as exc_info:  # Could be PALLoadError or PALValidationError
            loader.load_prompt_assembly(nonexistent_path)

        assert (
            "not found" in str(exc_info.value).lower()
            or "does not exist" in str(exc_info.value).lower()
        )

    def test_load_invalid_yaml_syntax(self, temp_dir):
        """Test loading file with invalid YAML syntax."""
        invalid_file = temp_dir / "invalid.pal"
        invalid_file.write_text("invalid: yaml: content: [")  # Unclosed bracket

        loader = Loader()
        with pytest.raises(PALValidationError) as exc_info:
            loader.load_prompt_assembly(invalid_file)

        assert "Invalid YAML syntax" in str(
            exc_info.value
        ) or "Failed to parse YAML" in str(exc_info.value)

    def test_load_invalid_pal_structure(self, temp_dir):
        """Test loading file with invalid PAL structure."""
        # Missing required fields
        invalid_content = {
            "pal_version": "1.0",
            # Missing id, version, description, composition
        }

        invalid_file = temp_dir / "invalid_structure.pal"
        with open(invalid_file, "w") as f:
            yaml.dump(invalid_content, f)

        loader = Loader()
        with pytest.raises(PALValidationError) as exc_info:
            loader.load_prompt_assembly(invalid_file)

        assert "Invalid prompt assembly format" in str(
            exc_info.value
        ) or "Validation failed" in str(exc_info.value)

    def test_load_invalid_library_structure(self, temp_dir):
        """Test loading library with invalid structure."""
        invalid_lib = {
            "pal_version": "1.0",
            "library_id": "invalid.lib",
            # Missing version, description, type, components
        }

        invalid_file = temp_dir / "invalid.pal.lib"
        with open(invalid_file, "w") as f:
            yaml.dump(invalid_lib, f)

        loader = Loader()
        with pytest.raises(PALValidationError) as exc_info:
            loader.load_component_library(invalid_file)

        assert "Invalid component library format" in str(
            exc_info.value
        ) or "Validation failed" in str(exc_info.value)


class TestCompilerExceptions:
    """Test exception handling in the PromptCompiler class."""

    @pytest.mark.asyncio
    async def test_missing_required_variables(self, temp_dir):
        """Test compilation with missing required variables."""
        variables = [
            PALVariable(
                name="required_var",
                type=VariableType.STRING,
                description="A required variable",
                required=True,
            ),
            PALVariable(
                name="another_required",
                type=VariableType.INTEGER,
                description="Another required variable",
                required=True,
            ),
        ]

        assembly = PromptAssembly(
            pal_version="1.0",
            id="test-prompt",
            version="1.0.0",
            description="Test prompt",
            variables=variables,
            composition=["{{ required_var }} and {{ another_required }}"],
        )

        compiler = PromptCompiler()

        # Provide only one of the required variables
        with pytest.raises(PALMissingVariableError) as exc_info:
            await compiler.compile(assembly, {"required_var": "value"})

        error = exc_info.value
        assert "Missing required variables" in str(error)
        assert error.context is not None
        assert "another_required" in error.context["missing_variables"]

    @pytest.mark.asyncio
    async def test_invalid_template_syntax(self):
        """Test compilation with invalid Jinja2 template syntax."""
        assembly = PromptAssembly(
            pal_version="1.0",
            id="invalid-template",
            version="1.0.0",
            description="Invalid template",
            composition=["{{ invalid template {{ syntax }}"],  # Invalid nested braces
        )

        compiler = PromptCompiler()

        with pytest.raises(PALCompilerError) as exc_info:
            await compiler.compile(assembly, {})

        error = exc_info.value
        assert "Template error" in str(error)
        assert error.context is not None
        assert "composition" in error.context

    @pytest.mark.asyncio
    async def test_type_conversion_error(self):
        """Test compilation with type conversion errors."""
        variables = [
            PALVariable(
                name="number_var",
                type=VariableType.INTEGER,
                description="A number variable",
            )
        ]

        assembly = PromptAssembly(
            pal_version="1.0",
            id="type-error-test",
            version="1.0.0",
            description="Type error test",
            variables=variables,
            composition=["Number: {{ number_var }}"],
        )

        compiler = PromptCompiler()

        with pytest.raises(PALCompilerError) as exc_info:
            await compiler.compile(assembly, {"number_var": "not_a_number"})

        error = exc_info.value
        assert "Type error for variable" in str(error)
        assert error.context is not None
        assert error.context["variable"] == "number_var"
        assert error.context["expected_type"] == VariableType.INTEGER

    @pytest.mark.asyncio
    async def test_missing_component_reference(self, temp_dir):
        """Test compilation with missing component references."""
        # Create a library with one component
        lib_content = {
            "pal_version": "1.0",
            "library_id": "test.lib",
            "version": "1.0.0",
            "description": "Test library",
            "type": "trait",
            "components": [
                {
                    "name": "existing_component",
                    "description": "An existing component",
                    "content": "Existing content",
                }
            ],
        }

        lib_file = temp_dir / "test.pal.lib"
        with open(lib_file, "w") as f:
            yaml.dump(lib_content, f)

        # Create assembly that references non-existent component
        assembly = PromptAssembly(
            pal_version="1.0",
            id="missing-comp-test",
            version="1.0.0",
            description="Missing component test",
            imports={"lib": str(lib_file)},
            composition=["{{ lib.nonexistent_component }}"],  # Component doesn't exist
        )

        compiler = PromptCompiler()

        with pytest.raises(PALMissingComponentError) as exc_info:
            await compiler.compile(assembly, {}, temp_dir)

        error = exc_info.value
        assert "Missing component references" in str(error)
        assert error.context is not None
        assert "errors" in error.context


class TestResolverExceptions:
    """Test exception handling in the Resolver class."""

    @pytest.mark.asyncio
    async def test_circular_dependency_detection(self, temp_dir):
        """Test circular dependency detection and error."""
        # Create library A that imports B
        lib_a_content = {
            "pal_version": "1.0",
            "library_id": "lib.a",
            "version": "1.0.0",
            "description": "Library A",
            "type": "trait",
            "components": [
                {"name": "comp_a", "description": "Component A", "content": "A"}
            ],
        }

        lib_a_file = temp_dir / "lib_a.pal.lib"
        with open(lib_a_file, "w") as f:
            yaml.dump(lib_a_content, f)

        # Create library B that imports A (creating a cycle)
        lib_b_content = {
            "pal_version": "1.0",
            "library_id": "lib.b",
            "version": "1.0.0",
            "description": "Library B",
            "type": "trait",
            "components": [
                {"name": "comp_b", "description": "Component B", "content": "B"}
            ],
        }

        lib_b_file = temp_dir / "lib_b.pal.lib"
        with open(lib_b_file, "w") as f:
            yaml.dump(lib_b_content, f)

        # Create assembly that creates circular dependency
        PromptAssembly(
            pal_version="1.0",
            id="circular-test",
            version="1.0.0",
            description="Circular dependency test",
            imports={"lib_a": str(lib_a_file), "lib_b": str(lib_b_file)},
            composition=["{{ lib_a.comp_a }} {{ lib_b.comp_b }}"],
        )

        # Manually set up circular dependency in resolver
        loader = Loader()
        resolver = Resolver(loader)

        # Add dependencies to create a cycle: circular-test -> lib.a -> lib.b -> circular-test
        resolver.dependency_graph.add_dependency("circular-test", "lib.a")
        resolver.dependency_graph.add_dependency("lib.a", "lib.b")
        resolver.dependency_graph.add_dependency("lib.b", "circular-test")

        with pytest.raises(PALCircularDependencyError) as exc_info:
            resolver.dependency_graph.check_cycles("circular-test")

        error = exc_info.value
        assert "Circular dependency detected" in str(error)
        assert error.context is not None
        assert "cycle" in error.context

    @pytest.mark.asyncio
    async def test_missing_dependency_file(self, temp_dir):
        """Test handling of missing dependency files."""
        assembly = PromptAssembly(
            pal_version="1.0",
            id="missing-dep-test",
            version="1.0.0",
            description="Missing dependency test",
            imports={"missing": str(temp_dir / "nonexistent.pal.lib")},
            composition=["{{ missing.component }}"],
        )

        loader = Loader()
        resolver = Resolver(loader)

        with pytest.raises(PALResolverError) as exc_info:
            await resolver.resolve_dependencies(assembly, temp_dir)

        error = exc_info.value
        assert "Failed to load dependency" in str(error)
        assert error.context is not None
        assert "path" in error.context
        assert "nonexistent.pal.lib" in error.context["path"]


class TestExecutorExceptions:
    """Test exception handling in the PromptExecutor class."""

    @pytest.mark.asyncio
    async def test_llm_client_failure(self):
        """Test handling of LLM client failures."""
        # Create a mock client that raises an exception
        failing_client = Mock()
        failing_client.generate_async.side_effect = Exception("API connection failed")

        assembly = PromptAssembly(
            pal_version="1.0",
            id="execution-test",
            version="1.0.0",
            description="Execution test",
            composition=["Test prompt"],
        )

        executor = PromptExecutor(failing_client)

        with pytest.raises(PALExecutorError) as exc_info:
            await executor.execute("Test prompt", assembly, "test-model")

        error = exc_info.value
        assert "Execution failed" in str(error)
        # The error context should contain execution information
        assert error.context is not None
        assert "error" in error.context


class TestEndToEndErrorHandling:
    """Test error handling in end-to-end scenarios."""

    @pytest.mark.asyncio
    async def test_complete_workflow_with_errors(self, temp_dir):
        """Test error propagation through complete workflow."""
        # Create a PAL file with multiple types of errors
        pal_content = {
            "pal_version": "1.0",
            "id": "error-prone-prompt",
            "version": "1.0.0",
            "description": "A prompt designed to trigger errors",
            "imports": {
                "nonexistent": str(temp_dir / "missing.pal.lib")  # Missing import
            },
            "variables": [
                {
                    "name": "required_var",
                    "type": "string",
                    "description": "Required variable",
                    "required": True,
                }
            ],
            "composition": [
                "{{ nonexistent.missing_component }}",  # Missing component
                "{{ required_var }}",  # Will be missing
                "{{ undefined_variable }}",  # Undefined variable
            ],
        }

        pal_file = temp_dir / "error_prone.pal"
        with open(pal_file, "w") as f:
            yaml.dump(pal_content, f)

        # Try to compile - should fail with resolver error first
        compiler = PromptCompiler()

        with pytest.raises(
            (PALResolverError, PALMissingVariableError, PALMissingComponentError)
        ):
            await compiler.compile_from_file(pal_file, {})

    def test_error_context_preservation(self):
        """Test that error contexts are properly preserved through the stack."""
        original_context = {
            "file": "test.pal",
            "line": 42,
            "details": "Detailed error information",
        }

        # Create a nested error scenario
        try:
            try:
                raise ValueError("Original error")
            except ValueError as e:
                raise PALCompilerError("Compilation failed", original_context) from e
        except PALCompilerError as final_error:
            assert final_error.context == original_context
            assert isinstance(final_error.__cause__, ValueError)
            assert "Original error" in str(final_error.__cause__)


class TestErrorRecovery:
    """Test error recovery and graceful degradation scenarios."""

    @pytest.mark.asyncio
    async def test_partial_success_with_optional_components(self, temp_dir):
        """Test graceful handling when optional components are missing."""
        # This test would be implemented if we had optional component loading
        # For now, we test that required components properly fail

        lib_content = {
            "pal_version": "1.0",
            "library_id": "partial.lib",
            "version": "1.0.0",
            "description": "Partially available library",
            "type": "trait",
            "components": [
                {
                    "name": "available_component",
                    "description": "Available component",
                    "content": "This component exists",
                }
            ],
        }

        lib_file = temp_dir / "partial.pal.lib"
        with open(lib_file, "w") as f:
            yaml.dump(lib_content, f)

        assembly = PromptAssembly(
            pal_version="1.0",
            id="partial-test",
            version="1.0.0",
            description="Partial availability test",
            imports={"partial": str(lib_file)},
            composition=[
                "{{ partial.available_component }}",  # Exists
                "{{ partial.missing_component }}",  # Doesn't exist
            ],
        )

        compiler = PromptCompiler()

        # Should fail because missing_component doesn't exist
        with pytest.raises(PALMissingComponentError):
            await compiler.compile(assembly, {}, temp_dir)
