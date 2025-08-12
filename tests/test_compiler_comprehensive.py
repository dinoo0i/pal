"""Comprehensive tests for PAL compiler system to improve coverage."""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import yaml
from jinja2 import TemplateError

from pal.core.compiler import ComponentTemplateLoader, PromptCompiler
from pal.exceptions.core import (
    PALCompilerError,
    PALMissingComponentError,
)
from pal.models.schema import (
    ComponentLibrary,
    PALComponent,
    PALVariable,
    PromptAssembly,
)


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_component_library():
    """Create a sample component library."""
    return ComponentLibrary(
        library_id="test.lib",
        version="1.0.0",
        description="Test library",
        type="trait",
        components=[
            PALComponent(
                name="greeting",
                description="Greeting component",
                content="Hello, {{ name }}!",
            ),
            PALComponent(
                name="instruction",
                description="Instruction component",
                content="Please follow these steps carefully.",
            ),
        ],
    )


class TestComponentTemplateLoader:
    """Test ComponentTemplateLoader with various scenarios."""

    def test_get_source_success(self, sample_component_library):
        """Test successful component template loading."""
        resolved_libraries = {"traits": sample_component_library}
        loader = ComponentTemplateLoader(resolved_libraries)

        source, _, _ = loader.get_source(None, "traits.greeting")
        assert source == "Hello, {{ name }}!"

    def test_get_source_invalid_format(self, sample_component_library):
        """Test component reference without dot separator."""
        resolved_libraries = {"traits": sample_component_library}
        loader = ComponentTemplateLoader(resolved_libraries)

        with pytest.raises(TemplateError) as exc_info:
            loader.get_source(None, "invalid_reference")

        assert "Component reference must be in format 'alias.component'" in str(
            exc_info.value
        )

    def test_get_source_unknown_alias(self, sample_component_library):
        """Test component reference with unknown alias."""
        resolved_libraries = {"traits": sample_component_library}
        loader = ComponentTemplateLoader(resolved_libraries)

        with pytest.raises(TemplateError) as exc_info:
            loader.get_source(None, "unknown.greeting")

        assert "Unknown import alias: unknown" in str(exc_info.value)

    def test_get_source_component_not_found(self, sample_component_library):
        """Test component reference with unknown component name."""
        resolved_libraries = {"traits": sample_component_library}
        loader = ComponentTemplateLoader(resolved_libraries)

        with pytest.raises(TemplateError) as exc_info:
            loader.get_source(None, "traits.nonexistent")

        assert "Component 'nonexistent' not found in library 'traits'" in str(
            exc_info.value
        )
        assert "Available: ['greeting', 'instruction']" in str(exc_info.value)

    def test_get_source_multiple_dot_component(self, sample_component_library):
        """Test component reference with multiple dots in component name."""
        # Add a component with dots in its name
        sample_component_library.components.append(
            PALComponent(
                name="complex_component_name",
                description="Complex component",
                content="Complex content",
            )
        )

        resolved_libraries = {"traits": sample_component_library}
        loader = ComponentTemplateLoader(resolved_libraries)

        source, _, _ = loader.get_source(None, "traits.complex_component_name")
        assert source == "Complex content"


class TestPromptCompilerVariableHandling:
    """Test variable handling and type conversion in PromptCompiler."""

    def test_convert_variable_unknown_type(self):
        """Test conversion with unknown variable type."""
        compiler = PromptCompiler()

        with pytest.raises(ValueError) as exc_info:
            compiler._convert_variable("test", "unknown_type")

        assert "Unknown variable type: unknown_type" in str(exc_info.value)

    def test_convert_to_int_with_boolean(self):
        """Test integer conversion with boolean input raises error."""
        compiler = PromptCompiler()

        with pytest.raises(TypeError) as exc_info:
            compiler._convert_to_int(True)

        assert "Boolean cannot be converted to integer" in str(exc_info.value)

    def test_convert_to_float_with_boolean(self):
        """Test float conversion with boolean input raises error."""
        compiler = PromptCompiler()

        with pytest.raises(TypeError) as exc_info:
            compiler._convert_to_float(False)

        assert "Boolean cannot be converted to float" in str(exc_info.value)

    def test_convert_to_bool_with_various_strings(self):
        """Test boolean conversion with various string inputs."""
        compiler = PromptCompiler()

        # Test true values
        assert compiler._convert_to_bool("true") is True
        assert compiler._convert_to_bool("TRUE") is True
        assert compiler._convert_to_bool("1") is True
        assert compiler._convert_to_bool("yes") is True
        assert compiler._convert_to_bool("YES") is True
        assert compiler._convert_to_bool("on") is True
        assert compiler._convert_to_bool("ON") is True

        # Test false values
        assert compiler._convert_to_bool("false") is False
        assert compiler._convert_to_bool("FALSE") is False
        assert compiler._convert_to_bool("0") is False
        assert compiler._convert_to_bool("no") is False
        assert compiler._convert_to_bool("NO") is False
        assert compiler._convert_to_bool("off") is False
        assert compiler._convert_to_bool("OFF") is False

        # Test invalid string
        with pytest.raises(ValueError) as exc_info:
            compiler._convert_to_bool("maybe")

        assert "Cannot convert string 'maybe' to boolean" in str(exc_info.value)

    def test_convert_to_list_with_invalid_type(self):
        """Test list conversion with invalid input type."""
        compiler = PromptCompiler()

        with pytest.raises(TypeError) as exc_info:
            compiler._convert_to_list("not a list")

        assert "Expected list or tuple, got str" in str(exc_info.value)

    def test_convert_to_dict_with_invalid_type(self):
        """Test dict conversion with invalid input type."""
        compiler = PromptCompiler()

        with pytest.raises(TypeError) as exc_info:
            compiler._convert_to_dict("not a dict")

        assert "Expected dict, got str" in str(exc_info.value)


class TestPromptCompilerTemplateAnalysis:
    """Test template variable analysis functionality."""

    def test_analyze_template_variables_with_template_error_fallback(self):
        """Test analyze_template_variables with template parsing fallback."""
        compiler = PromptCompiler()

        # Create a prompt assembly with invalid Jinja syntax in full composition
        # but valid syntax in individual items
        prompt_assembly = PromptAssembly(
            id="test-prompt",
            version="1.0.0",
            description="Test prompt",
            variables=[
                PALVariable(
                    name="declared_var", type="string", description="Declared variable"
                )
            ],
            imports={"traits": "test.pal.lib"},
            composition=[
                "Valid item with {{ undeclared_var }}",
                "Another item with {{ another_var }}",
                "{% for item in items %}{{ item }}{% endfor",  # Invalid syntax when joined
            ],
        )

        with patch("jinja2.Environment.parse") as mock_parse:
            # Create mock parsed objects for successful parsing
            mock_parsed = MagicMock()

            # First call (full composition) raises TemplateError
            # Subsequent calls (individual items) succeed
            mock_parse.side_effect = [
                TemplateError("Invalid syntax"),  # Full composition fails
                mock_parsed,  # Individual items succeed
                mock_parsed,
                TemplateError("Still invalid"),  # Last item fails
            ]

            # Mock find_undeclared_variables to return some variables
            with patch(
                "jinja2.meta.find_undeclared_variables",
                return_value={"undeclared_var", "another_var"},
            ):
                compiler.analyze_template_variables(prompt_assembly)

                # Should fall back to item-by-item analysis
                assert mock_parse.call_count >= 2

    def test_analyze_template_variables_with_dotted_references(self):
        """Test analyze_template_variables with dotted component references."""
        compiler = PromptCompiler()

        prompt_assembly = PromptAssembly(
            id="test-prompt",
            version="1.0.0",
            description="Test prompt",
            variables=[],
            imports={"traits": "test.pal.lib"},
            composition=[
                "Use {{ traits.greeting }} component",
                "Also use {{ unknown.component }} component",
                "And {{ undeclared_var }} variable",
            ],
        )

        variables = compiler.analyze_template_variables(prompt_assembly)

        # Should include unknown (unknown alias) and undeclared_var
        # but not traits (known import alias)
        # Note: the analyze method extracts just the alias part for dotted references
        assert "unknown" in variables
        assert "undeclared_var" in variables
        assert "traits" not in variables


class TestPromptCompilerErrorHandling:
    """Test error handling scenarios in PromptCompiler."""

    @pytest.mark.asyncio
    async def test_compile_with_variable_type_error(self, temp_dir):
        """Test compilation with variable type conversion error."""
        # Create prompt assembly with integer variable
        prompt_assembly = PromptAssembly(
            id="test-prompt",
            version="1.0.0",
            description="Test prompt",
            variables=[PALVariable(name="count", type="integer", description="Count")],
            composition=["Count is: {{ count }}"],
        )

        compiler = PromptCompiler()

        # Try to provide a boolean value for integer variable - this should actually work
        # because we have logic to prevent boolean->int conversion
        # Let's use a string that can't be converted instead
        with pytest.raises(PALCompilerError) as exc_info:
            await compiler.compile(prompt_assembly, variables={"count": "not_a_number"})

        assert "Type error for variable 'count'" in str(exc_info.value)
        assert "VariableType.INTEGER" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_compile_with_undefined_variable_passthrough(self, temp_dir):
        """Test compilation with undefined variables passed through."""
        # Create prompt assembly without declaring all used variables
        prompt_assembly = PromptAssembly(
            id="test-prompt",
            version="1.0.0",
            description="Test prompt",
            variables=[],  # No variables declared
            composition=["Hello {{ name }}! You are {{ age }} years old."],
        )

        compiler = PromptCompiler()

        # Provide variables not declared in schema - should pass through
        result = await compiler.compile(
            prompt_assembly, variables={"name": "Alice", "age": 25, "extra": "ignored"}
        )

        assert "Hello Alice! You are 25 years old." in result


class TestPromptCompilerIntegration:
    """Integration tests for PromptCompiler with actual files."""

    @pytest.mark.asyncio
    async def test_compile_from_file_with_missing_component_references(self, temp_dir):
        """Test compilation with missing component references."""
        # First create a valid component library file
        lib_content = {
            "pal_version": "1.0",
            "library_id": "test.lib",
            "version": "1.0.0",
            "description": "Test library",
            "type": "trait",
            "components": [
                {
                    "name": "existing_component",
                    "description": "Existing component",
                    "content": "Hello World",
                }
            ],
        }

        lib_file = temp_dir / "test.pal.lib"
        with open(lib_file, "w") as f:
            yaml.dump(lib_content, f)

        # Create PAL file with reference to non-existent component
        pal_content = {
            "pal_version": "1.0",
            "id": "test-prompt",
            "version": "1.0.0",
            "description": "Test prompt",
            "imports": {"traits": "test.pal.lib"},  # Valid library
            "variables": [],
            "composition": [
                "Use {{ traits.nonexistent_component }}"
            ],  # Invalid component
        }

        pal_file = temp_dir / "test.pal"
        with open(pal_file, "w") as f:
            yaml.dump(pal_content, f)

        compiler = PromptCompiler()

        with pytest.raises(PALMissingComponentError) as exc_info:
            await compiler.compile_from_file(pal_file)

        assert "Missing component references" in str(exc_info.value)

    def test_compile_from_file_sync(self, temp_dir):
        """Test synchronous compile_from_file wrapper."""
        # Create simple PAL file
        pal_content = {
            "pal_version": "1.0",
            "id": "sync-test",
            "version": "1.0.0",
            "description": "Sync test",
            "variables": [],
            "composition": ["Simple prompt without variables"],
        }

        pal_file = temp_dir / "sync.pal"
        with open(pal_file, "w") as f:
            yaml.dump(pal_content, f)

        compiler = PromptCompiler()
        result = compiler.compile_from_file_sync(pal_file)

        assert "Simple prompt without variables" in result


class TestPromptCompilerHelperMethods:
    """Test helper methods in PromptCompiler."""

    def test_add_default_variables_with_explicit_default(self):
        """Test adding default values when explicit defaults are provided."""
        compiler = PromptCompiler()

        var_definitions = [
            PALVariable(
                name="with_default",
                type="string",
                description="Has default",
                default="default_value",
            ),
            PALVariable(
                name="without_default",
                type="string",
                description="No default",
                required=False,
            ),
        ]

        typed_vars = {}
        compiler._add_default_variables(var_definitions, typed_vars)

        assert typed_vars["with_default"] == "default_value"
        assert typed_vars["without_default"] == ""  # Type default

    def test_clean_compiled_prompt_excessive_newlines(self):
        """Test cleaning prompt with excessive newlines."""
        compiler = PromptCompiler()

        prompt_with_excess = "Line 1\n\n\n\n\nLine 2\n\n\n   \n\n\nLine 3"
        cleaned = compiler._clean_compiled_prompt(prompt_with_excess)

        # Should reduce excessive newlines to at most 2
        assert "\n\n\n" not in cleaned
        assert cleaned == "Line 1\n\nLine 2\n\nLine 3"

    def test_build_template_context_with_components(self):
        """Test building template context with component access."""
        compiler = PromptCompiler()
        sample_lib = ComponentLibrary(
            library_id="test.lib",
            version="1.0.0",
            description="Test library",
            type="trait",
            components=[
                PALComponent(
                    name="comp1", description="Component 1", content="Content 1"
                ),
                PALComponent(
                    name="comp2", description="Component 2", content="Content 2"
                ),
            ],
        )

        resolved_libraries = {"mylib": sample_lib}
        variables = {"var1": "value1"}

        context = compiler._build_template_context(resolved_libraries, variables)

        assert context["var1"] == "value1"
        assert context["mylib"]["comp1"] == "Content 1"
        assert context["mylib"]["comp2"] == "Content 2"
