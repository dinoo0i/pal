"""Basic tests to verify PAL functionality."""

import json
import tempfile
from pathlib import Path

import pytest

from pal import (
    ComponentLibrary,
    Loader,
    MockLLMClient,
    PALValidationError,
    PromptAssembly,
    PromptCompiler,
    PromptExecutor,
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
        "library_id": "test.library",
        "version": "1.0.0",
        "description": "Test library",
        "type": "trait",
        "components": [
            {
                "name": "test_component",
                "description": "A test component",
                "content": "You are a test assistant.",
            }
        ],
    }

    lib_file = temp_dir / "test.pal.lib"
    with open(lib_file, "w") as f:
        import yaml

        yaml.dump(lib_content, f)

    return lib_file


@pytest.fixture
def sample_prompt(temp_dir, sample_library):
    """Create a sample prompt assembly."""
    prompt_content = {
        "pal_version": "1.0",
        "id": "test-prompt",
        "version": "1.0.0",
        "description": "Test prompt",
        "imports": {"test_lib": str(sample_library)},
        "variables": [
            {"name": "user_input", "type": "string", "description": "User input"}
        ],
        "composition": ["{{ test_lib.test_component }}", "User says: {{ user_input }}"],
    }

    prompt_file = temp_dir / "test.pal"
    with open(prompt_file, "w") as f:
        import yaml

        yaml.dump(prompt_content, f)

    return prompt_file


class TestLoader:
    """Test the PAL loader functionality."""

    def test_load_component_library(self, sample_library):
        """Test loading a component library."""
        loader = Loader()
        library = loader.load_component_library(sample_library)

        assert isinstance(library, ComponentLibrary)
        assert library.library_id == "test.library"
        assert library.version == "1.0.0"
        assert len(library.components) == 1
        assert library.components[0].name == "test_component"

    def test_load_prompt_assembly(self, sample_prompt):
        """Test loading a prompt assembly."""
        loader = Loader()
        assembly = loader.load_prompt_assembly(sample_prompt)

        assert isinstance(assembly, PromptAssembly)
        assert assembly.id == "test-prompt"
        assert assembly.version == "1.0.0"
        assert len(assembly.imports) == 1
        assert len(assembly.variables) == 1
        assert len(assembly.composition) == 2

    def test_invalid_yaml(self, temp_dir):
        """Test handling of invalid YAML."""
        invalid_file = temp_dir / "invalid.pal"
        invalid_file.write_text("invalid: yaml: content:")

        loader = Loader()
        with pytest.raises(PALValidationError):
            loader.load_prompt_assembly(invalid_file)


class TestCompiler:
    """Test the PAL compiler functionality."""

    @pytest.mark.asyncio
    async def test_compile_prompt(self, sample_prompt):
        """Test compiling a prompt assembly."""
        compiler = PromptCompiler()
        variables = {"user_input": "Hello, world!"}

        compiled = await compiler.compile_from_file(sample_prompt, variables)

        assert "You are a test assistant." in compiled
        assert "User says: Hello, world!" in compiled

    @pytest.mark.asyncio
    async def test_missing_variable_error(self, sample_prompt):
        """Test error when required variables are missing."""
        compiler = PromptCompiler()

        # Don't provide required variable
        with pytest.raises(Exception):  # Should raise PALMissingVariableError
            await compiler.compile_from_file(sample_prompt, {})

    def test_sync_compile(self, sample_prompt):
        """Test synchronous compilation."""
        compiler = PromptCompiler()
        variables = {"user_input": "Hello, sync world!"}

        compiled = compiler.compile_from_file_sync(sample_prompt, variables)

        assert "You are a test assistant." in compiled
        assert "User says: Hello, sync world!" in compiled


class TestExecutor:
    """Test the PAL executor functionality."""

    @pytest.mark.asyncio
    async def test_mock_execution(self, sample_prompt):
        """Test execution with mock LLM client."""
        compiler = PromptCompiler()
        llm_client = MockLLMClient("Mock response from test")
        executor = PromptExecutor(llm_client)

        # Load and compile
        loader = Loader()
        assembly = await loader.load_prompt_assembly_async(sample_prompt)
        compiled = await compiler.compile(assembly, {"user_input": "test input"})

        # Execute
        result = await executor.execute(compiled, assembly, "test-model")

        assert result.success is True
        assert result.response == "Mock response from test"
        assert result.prompt_id == "test-prompt"
        assert result.model == "test-model"
        assert result.execution_time_ms > 0


class TestEndToEnd:
    """End-to-end integration tests."""

    @pytest.mark.asyncio
    async def test_full_workflow(self, sample_prompt):
        """Test the complete PAL workflow."""
        # Set up components
        loader = Loader()
        compiler = PromptCompiler(loader)
        llm_client = MockLLMClient("Complete workflow response")
        executor = PromptExecutor(llm_client)

        # Load prompt assembly
        assembly = await loader.load_prompt_assembly_async(sample_prompt)

        # Compile with variables
        variables = {"user_input": "End-to-end test"}
        compiled = await compiler.compile(assembly, variables, sample_prompt)

        # Execute
        result = await executor.execute(compiled, assembly, "workflow-test-model")

        # Verify results
        assert "You are a test assistant." in compiled
        assert "End-to-end test" in compiled
        assert result.success is True
        assert result.response == "Complete workflow response"

        # Check execution history
        history = executor.get_execution_history()
        assert len(history) == 1
        assert history[0].prompt_id == "test-prompt"


if __name__ == "__main__":
    pytest.main([__file__])
