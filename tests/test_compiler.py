"""Tests for PAL compiler functionality including Jinja2 templating and variable analysis."""

import tempfile
from pathlib import Path

import pytest
import yaml

from pal.core.compiler import PromptCompiler
from pal.exceptions.core import PALCompilerError, PALMissingVariableError
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


@pytest.fixture
def sample_library(temp_dir):
    """Create a sample component library."""
    lib_content = {
        "pal_version": "1.0",
        "library_id": "test.components",
        "version": "1.0.0",
        "description": "Test components",
        "type": "trait",
        "components": [
            {
                "name": "greeting",
                "description": "A greeting component",
                "content": "Hello, I am your assistant.",
            },
            {
                "name": "analytical_mode",
                "description": "Analytical thinking mode",
                "content": "I will think step by step and analyze this problem carefully.",
            },
            {
                "name": "json_format",
                "description": "JSON output format",
                "content": "Please respond in valid JSON format with the following structure:",
            },
        ],
    }

    lib_file = temp_dir / "components.pal.lib"
    with open(lib_file, "w") as f:
        yaml.dump(lib_content, f)

    return lib_file


class TestVariableTypeConversion:
    """Test variable type conversion functionality."""

    def test_string_conversion(self):
        """Test string type conversion."""
        compiler = PromptCompiler()

        assert compiler._convert_variable("hello", VariableType.STRING) == "hello"
        assert compiler._convert_variable(123, VariableType.STRING) == "123"
        assert compiler._convert_variable(True, VariableType.STRING) == "True"

    def test_integer_conversion(self):
        """Test integer type conversion."""
        compiler = PromptCompiler()

        assert compiler._convert_variable(42, VariableType.INTEGER) == 42
        assert compiler._convert_variable("123", VariableType.INTEGER) == 123
        assert compiler._convert_variable(45.7, VariableType.INTEGER) == 45

        # Boolean should not be converted to integer
        with pytest.raises(TypeError):
            compiler._convert_variable(True, VariableType.INTEGER)

    def test_float_conversion(self):
        """Test float type conversion."""
        compiler = PromptCompiler()

        assert compiler._convert_variable(3.14, VariableType.FLOAT) == 3.14
        assert compiler._convert_variable("2.5", VariableType.FLOAT) == 2.5
        assert compiler._convert_variable(42, VariableType.FLOAT) == 42.0

        # Boolean should not be converted to float
        with pytest.raises(TypeError):
            compiler._convert_variable(False, VariableType.FLOAT)

    def test_boolean_conversion(self):
        """Test boolean type conversion."""
        compiler = PromptCompiler()

        # Direct boolean values
        assert compiler._convert_variable(True, VariableType.BOOLEAN) is True
        assert compiler._convert_variable(False, VariableType.BOOLEAN) is False

        # String conversions
        assert compiler._convert_variable("true", VariableType.BOOLEAN) is True
        assert compiler._convert_variable("TRUE", VariableType.BOOLEAN) is True
        assert compiler._convert_variable("1", VariableType.BOOLEAN) is True
        assert compiler._convert_variable("yes", VariableType.BOOLEAN) is True
        assert compiler._convert_variable("on", VariableType.BOOLEAN) is True

        assert compiler._convert_variable("false", VariableType.BOOLEAN) is False
        assert compiler._convert_variable("FALSE", VariableType.BOOLEAN) is False
        assert compiler._convert_variable("0", VariableType.BOOLEAN) is False
        assert compiler._convert_variable("no", VariableType.BOOLEAN) is False
        assert compiler._convert_variable("off", VariableType.BOOLEAN) is False

        # Invalid string
        with pytest.raises(ValueError):
            compiler._convert_variable("maybe", VariableType.BOOLEAN)

    def test_list_conversion(self):
        """Test list type conversion."""
        compiler = PromptCompiler()

        assert compiler._convert_variable([1, 2, 3], VariableType.LIST) == [1, 2, 3]
        assert compiler._convert_variable((1, 2, 3), VariableType.LIST) == [1, 2, 3]

        # Non-list should fail
        with pytest.raises(TypeError):
            compiler._convert_variable("not a list", VariableType.LIST)

    def test_dict_conversion(self):
        """Test dict type conversion."""
        compiler = PromptCompiler()

        test_dict = {"key": "value", "num": 42}
        assert compiler._convert_variable(test_dict, VariableType.DICT) == test_dict

        # Non-dict should fail
        with pytest.raises(TypeError):
            compiler._convert_variable([1, 2, 3], VariableType.DICT)

    def test_any_conversion(self):
        """Test ANY type conversion (should pass through unchanged)."""
        compiler = PromptCompiler()

        test_values = ["string", 42, 3.14, True, [1, 2, 3], {"key": "value"}]
        for value in test_values:
            assert compiler._convert_variable(value, VariableType.ANY) == value


class TestTemplateCompilation:
    """Test Jinja2 template compilation."""

    @pytest.mark.asyncio
    async def test_simple_variable_substitution(self, sample_library):
        """Test simple variable substitution in templates."""
        variables = [
            PALVariable(name="name", type=VariableType.STRING, description="User name")
        ]

        assembly = PromptAssembly(
            pal_version="1.0",
            id="simple-test",
            version="1.0.0",
            description="Simple test",
            variables=variables,
            composition=["Hello, {{ name }}!"],
        )

        compiler = PromptCompiler()
        result = await compiler.compile(assembly, {"name": "Alice"})

        assert result == "Hello, Alice!"

    @pytest.mark.asyncio
    async def test_component_inclusion(self, sample_library):
        """Test including components from libraries."""
        assembly = PromptAssembly(
            pal_version="1.0",
            id="component-test",
            version="1.0.0",
            description="Component test",
            imports={"comp": str(sample_library)},
            composition=["{{ comp.greeting }}", "How can I help you?"],
        )

        compiler = PromptCompiler()
        result = await compiler.compile(assembly, {}, sample_library.parent)

        assert "Hello, I am your assistant." in result
        assert "How can I help you?" in result

    @pytest.mark.asyncio
    async def test_jinja_loops(self, sample_library):
        """Test Jinja2 for loops in composition."""
        variables = [
            PALVariable(
                name="items", type=VariableType.LIST, description="List of items"
            )
        ]

        assembly = PromptAssembly(
            pal_version="1.0",
            id="loop-test",
            version="1.0.0",
            description="Loop test",
            variables=variables,
            composition=[
                "Items:",
                "{% for item in items %}",
                "- {{ item }}",
                "{% endfor %}",
            ],
        )

        compiler = PromptCompiler()
        result = await compiler.compile(
            assembly, {"items": ["apple", "banana", "cherry"]}
        )

        expected_lines = ["Items:", "- apple", "- banana", "- cherry"]
        for line in expected_lines:
            assert line in result

    @pytest.mark.asyncio
    async def test_jinja_conditionals(self, sample_library):
        """Test Jinja2 conditional statements."""
        variables = [
            PALVariable(
                name="show_greeting",
                type=VariableType.BOOLEAN,
                description="Whether to show greeting",
            )
        ]

        assembly = PromptAssembly(
            pal_version="1.0",
            id="conditional-test",
            version="1.0.0",
            description="Conditional test",
            imports={"comp": str(sample_library)},
            variables=variables,
            composition=[
                "{% if show_greeting %}",
                "{{ comp.greeting }}",
                "{% endif %}",
                "Main content here.",
            ],
        )

        compiler = PromptCompiler()

        # Test with greeting enabled
        result_with_greeting = await compiler.compile(
            assembly, {"show_greeting": True}, sample_library.parent
        )
        assert "Hello, I am your assistant." in result_with_greeting
        assert "Main content here." in result_with_greeting

        # Test with greeting disabled
        result_without_greeting = await compiler.compile(
            assembly, {"show_greeting": False}, sample_library.parent
        )
        assert "Hello, I am your assistant." not in result_without_greeting
        assert "Main content here." in result_without_greeting

    @pytest.mark.asyncio
    async def test_jinja_filters(self, sample_library):
        """Test Jinja2 built-in filters."""
        variables = [
            PALVariable(
                name="text", type=VariableType.STRING, description="Text to transform"
            )
        ]

        assembly = PromptAssembly(
            pal_version="1.0",
            id="filter-test",
            version="1.0.0",
            description="Filter test",
            variables=variables,
            composition=[
                "Original: {{ text }}",
                "Upper: {{ text|upper }}",
                "Lower: {{ text|lower }}",
                "Title: {{ text|title }}",
            ],
        )

        compiler = PromptCompiler()
        result = await compiler.compile(assembly, {"text": "hello WORLD"})

        assert "Original: hello WORLD" in result
        assert "Upper: HELLO WORLD" in result
        assert "Lower: hello world" in result
        assert "Title: Hello World" in result


class TestVariableAnalysis:
    """Test template variable analysis functionality."""

    def test_analyze_simple_variables(self):
        """Test analysis of simple template variables."""
        assembly = PromptAssembly(
            pal_version="1.0",
            id="var-analysis-test",
            version="1.0.0",
            description="Variable analysis test",
            composition=[
                "Hello {{ name }}!",
                "You are {{ age }} years old.",
                "Your email is {{ email }}.",
            ],
        )

        compiler = PromptCompiler()
        variables = compiler.analyze_template_variables(assembly)

        expected = {"name", "age", "email"}
        assert variables == expected

    def test_analyze_with_defined_variables(self):
        """Test that defined variables are excluded from analysis."""
        variables = [
            PALVariable(name="name", type=VariableType.STRING, description="Name"),
            PALVariable(name="age", type=VariableType.INTEGER, description="Age"),
        ]

        assembly = PromptAssembly(
            pal_version="1.0",
            id="defined-vars-test",
            version="1.0.0",
            description="Defined variables test",
            variables=variables,
            composition=[
                "Hello {{ name }}!",  # Defined - should be excluded
                "You are {{ age }} years old.",  # Defined - should be excluded
                "Your email is {{ email }}.",  # Not defined - should be included
            ],
        )

        compiler = PromptCompiler()
        undeclared_vars = compiler.analyze_template_variables(assembly)

        # Only email should be undeclared
        assert undeclared_vars == {"email"}

    def test_analyze_with_component_imports(self):
        """Test that component import aliases are excluded from analysis."""
        assembly = PromptAssembly(
            pal_version="1.0",
            id="import-test",
            version="1.0.0",
            description="Import test",
            imports={
                "traits": "path/to/traits.pal.lib",
                "formats": "path/to/formats.pal.lib",
            },
            composition=[
                "{{ traits.helpful }}",  # Import alias - should be excluded
                "{{ formats.json }}",  # Import alias - should be excluded
                "User says: {{ user_input }}",  # Variable - should be included
            ],
        )

        compiler = PromptCompiler()
        variables = compiler.analyze_template_variables(assembly)

        # Only user_input should be undeclared
        assert variables == {"user_input"}

    def test_analyze_with_loops(self):
        """Test analysis with Jinja2 loop constructs."""
        assembly = PromptAssembly(
            pal_version="1.0",
            id="loop-analysis-test",
            version="1.0.0",
            description="Loop analysis test",
            composition=[
                "Items: {{ items|length }}",
                "{% for item in items %}",
                "- {{ item.name }}: {{ item.value }}",
                "{% endfor %}",
                "Total: {{ total }}",
            ],
        )

        compiler = PromptCompiler()
        variables = compiler.analyze_template_variables(assembly)

        # Should include items and total, but not item (loop variable)
        expected = {"items", "total"}
        assert variables == expected


class TestMissingVariableValidation:
    """Test missing variable validation."""

    @pytest.mark.asyncio
    async def test_missing_required_variable(self):
        """Test error when required variable is missing."""
        variables = [
            PALVariable(
                name="required_var",
                type=VariableType.STRING,
                description="A required variable",
                required=True,
            )
        ]

        assembly = PromptAssembly(
            pal_version="1.0",
            id="missing-var-test",
            version="1.0.0",
            description="Missing variable test",
            variables=variables,
            composition=["Value: {{ required_var }}"],
        )

        compiler = PromptCompiler()

        with pytest.raises(PALMissingVariableError) as exc_info:
            await compiler.compile(assembly, {})  # No variables provided

        assert "Missing required variables" in str(exc_info.value)
        assert "required_var" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_optional_variable_with_default(self):
        """Test that optional variables with defaults work correctly."""
        variables = [
            PALVariable(
                name="optional_var",
                type=VariableType.STRING,
                description="An optional variable",
                required=False,
                default="default_value",
            )
        ]

        assembly = PromptAssembly(
            pal_version="1.0",
            id="default-var-test",
            version="1.0.0",
            description="Default variable test",
            variables=variables,
            composition=["Value: {{ optional_var }}"],
        )

        compiler = PromptCompiler()
        result = await compiler.compile(assembly, {})  # No variables provided

        assert "Value: default_value" in result

    @pytest.mark.asyncio
    async def test_optional_variable_without_default(self):
        """Test that optional variables without defaults work correctly."""
        variables = [
            PALVariable(
                name="optional_str",
                type=VariableType.STRING,
                description="An optional string variable",
                required=False,
            ),
            PALVariable(
                name="optional_list",
                type=VariableType.LIST,
                description="An optional list variable",
                required=False,
            ),
        ]

        assembly = PromptAssembly(
            pal_version="1.0",
            id="optional-no-default-test",
            version="1.0.0",
            description="Optional variable without default test",
            variables=variables,
            composition=[
                "{% if optional_str %}String: {{ optional_str }}{% endif %}",
                "{% if optional_list %}List: {{ optional_list }}{% endif %}",
                "Always shown text",
            ],
        )

        compiler = PromptCompiler()
        result = await compiler.compile(assembly, {})  # No variables provided

        # Optional variables should be empty but not cause errors
        assert "String:" not in result  # Empty string is falsy
        assert "List:" not in result  # Empty list is falsy
        assert "Always shown text" in result

        # Test with values provided
        result_with_values = await compiler.compile(
            assembly,
            {"optional_str": "test value", "optional_list": ["item1", "item2"]},
        )

        assert "String: test value" in result_with_values
        assert "List: ['item1', 'item2']" in result_with_values
        assert "Always shown text" in result_with_values


class TestErrorHandling:
    """Test error handling in compilation."""

    @pytest.mark.asyncio
    async def test_invalid_jinja_syntax(self):
        """Test handling of invalid Jinja2 syntax."""
        assembly = PromptAssembly(
            pal_version="1.0",
            id="invalid-syntax-test",
            version="1.0.0",
            description="Invalid syntax test",
            composition=["{{ invalid {{ nested }} }}"],  # Invalid nested braces
        )

        compiler = PromptCompiler()

        with pytest.raises(PALCompilerError) as exc_info:
            await compiler.compile(assembly, {})

        assert "Template error" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_type_error_in_variable_conversion(self):
        """Test handling of type conversion errors."""
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

        assert "Type error for variable" in str(exc_info.value)
        assert "expected VariableType.INTEGER" in str(exc_info.value)


class TestPromptCleaning:
    """Test prompt cleaning functionality."""

    def test_clean_excessive_blank_lines(self):
        """Test cleaning of excessive blank lines."""
        compiler = PromptCompiler()

        messy_prompt = "Line 1\n\n\n\n\nLine 2\n\n\n\nLine 3"
        cleaned = compiler._clean_compiled_prompt(messy_prompt)

        # Should reduce multiple blank lines to at most 2
        assert "\n\n\n" not in cleaned
        assert cleaned == "Line 1\n\nLine 2\n\nLine 3"

    def test_clean_leading_trailing_whitespace(self):
        """Test cleaning of leading and trailing whitespace."""
        compiler = PromptCompiler()

        messy_prompt = "   \n\n  Content here  \n\n   "
        cleaned = compiler._clean_compiled_prompt(messy_prompt)

        assert cleaned == "Content here"
