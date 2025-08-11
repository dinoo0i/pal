"""Tests for PAL CLI commands and integration."""

import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
import yaml
from click.testing import CliRunner

from pal.cli.main import cli
from pal.models.schema import ExecutionResult


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_pal_setup(temp_dir):
    """Create a complete PAL setup for testing."""
    # Create component library
    lib_content = {
        "pal_version": "1.0",
        "library_id": "cli.test",
        "version": "1.0.0",
        "description": "CLI test library",
        "type": "trait",
        "components": [
            {
                "name": "helpful_assistant",
                "description": "Helpful assistant trait",
                "content": "I am a helpful AI assistant.",
            },
            {
                "name": "json_format",
                "description": "JSON response format",
                "content": "Please respond in JSON format with the following structure:",
            },
        ],
    }

    lib_file = temp_dir / "test.pal.lib"
    with open(lib_file, "w") as f:
        yaml.dump(lib_content, f)

    # Create PAL prompt
    pal_content = {
        "pal_version": "1.0",
        "id": "cli-test-prompt",
        "version": "1.0.0",
        "description": "CLI test prompt",
        "author": "Test Suite",
        "imports": {"traits": str(lib_file)},
        "variables": [
            {
                "name": "user_query",
                "type": "string",
                "description": "User query to process",
                "required": True,
            },
            {
                "name": "format",
                "type": "string",
                "description": "Response format",
                "required": False,
                "default": "text",
            },
        ],
        "composition": [
            "{{ traits.helpful_assistant }}",
            "",
            "{% if format == 'json' %}",
            "{{ traits.json_format }}",
            "{% endif %}",
            "",
            "User Query: {{ user_query }}",
            "Please provide a helpful response.",
        ],
    }

    pal_file = temp_dir / "test.pal"
    with open(pal_file, "w") as f:
        yaml.dump(pal_content, f)

    # Create evaluation suite
    eval_content = {
        "pal_version": "1.0",
        "prompt_id": "cli-test-prompt",
        "target_version": "1.0.0",
        "description": "CLI test evaluation",
        "test_cases": [
            {
                "name": "basic_response_test",
                "description": "Test basic response functionality",
                "variables": {
                    "user_query": "What is machine learning?",
                    "format": "text",
                },
                "assertions": [
                    {
                        "type": "length",
                        "config": {"min_length": 20, "max_length": 1000},
                    },
                    {
                        "type": "contains",
                        "config": {"text": "helpful", "case_sensitive": False},
                    },
                ],
            },
            {
                "name": "json_format_test",
                "description": "Test JSON format response",
                "variables": {"user_query": "Explain AI briefly", "format": "json"},
                "assertions": [
                    {"type": "json_valid", "config": {}},
                    {
                        "type": "contains",
                        "config": {"text": "JSON format", "case_sensitive": False},
                    },
                ],
            },
        ],
    }

    eval_file = temp_dir / "test.eval.yaml"
    with open(eval_file, "w") as f:
        yaml.dump(eval_content, f)

    return {
        "pal_file": pal_file,
        "lib_file": lib_file,
        "eval_file": eval_file,
        "temp_dir": temp_dir,
    }


class TestCLIBasicCommands:
    """Test basic CLI command functionality."""

    def test_cli_help(self):
        """Test CLI help command."""
        runner = CliRunner()
        result = runner.invoke(cli, ["--help"])

        assert result.exit_code == 0
        assert "PAL - Prompt Assembly Language CLI" in result.output
        assert "compile" in result.output
        assert "execute" in result.output
        assert "validate" in result.output
        assert "info" in result.output
        assert "evaluate" in result.output

    def test_command_help(self):
        """Test individual command help."""
        runner = CliRunner()

        commands = ["compile", "execute", "validate", "info", "evaluate"]
        for command in commands:
            result = runner.invoke(cli, [command, "--help"])
            assert result.exit_code == 0
            assert command in result.output.lower()


class TestCompileCommand:
    """Test the compile CLI command."""

    def test_compile_basic(self, sample_pal_setup):
        """Test basic compilation."""
        runner = CliRunner()
        pal_file = sample_pal_setup["pal_file"]

        result = runner.invoke(
            cli,
            [
                "compile",
                str(pal_file),
                "--vars",
                '{"user_query": "Hello world"}',
                "--no-format",
            ],
        )

        assert result.exit_code == 0
        assert "I am a helpful AI assistant" in result.output
        assert "User Query: Hello world" in result.output

    def test_compile_with_vars_file(self, sample_pal_setup):
        """Test compilation with variables from file."""
        temp_dir = sample_pal_setup["temp_dir"]
        pal_file = sample_pal_setup["pal_file"]

        # Create variables file
        variables = {"user_query": "Test from file", "format": "json"}
        vars_file = temp_dir / "vars.json"
        with open(vars_file, "w") as f:
            json.dump(variables, f)

        runner = CliRunner()
        result = runner.invoke(
            cli,
            ["compile", str(pal_file), "--vars-file", str(vars_file), "--no-format"],
        )

        assert result.exit_code == 0
        assert "Test from file" in result.output
        assert "JSON format" in result.output

    def test_compile_with_output_file(self, sample_pal_setup):
        """Test compilation with output to file."""
        temp_dir = sample_pal_setup["temp_dir"]
        pal_file = sample_pal_setup["pal_file"]
        output_file = temp_dir / "compiled.txt"

        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "compile",
                str(pal_file),
                "--vars",
                '{"user_query": "Output test"}',
                "--output",
                str(output_file),
            ],
        )

        assert result.exit_code == 0
        assert f"Compiled prompt written to {output_file}" in result.output

        # Check output file content
        assert output_file.exists()
        content = output_file.read_text()
        assert "Output test" in content

    def test_compile_missing_variables(self, sample_pal_setup):
        """Test compilation with missing required variables."""
        runner = CliRunner()
        pal_file = sample_pal_setup["pal_file"]

        result = runner.invoke(cli, ["compile", str(pal_file)])

        assert result.exit_code == 1
        assert "Error:" in result.output

    def test_compile_invalid_json_vars(self, sample_pal_setup):
        """Test compilation with invalid JSON in vars."""
        runner = CliRunner()
        pal_file = sample_pal_setup["pal_file"]

        result = runner.invoke(
            cli, ["compile", str(pal_file), "--vars", "invalid json"]
        )

        assert result.exit_code == 1
        assert "Invalid JSON" in result.output


class TestExecuteCommand:
    """Test the execute CLI command."""

    def test_execute_with_mock(self, sample_pal_setup):
        """Test execution with mock provider."""
        runner = CliRunner()
        pal_file = sample_pal_setup["pal_file"]

        result = runner.invoke(
            cli,
            [
                "execute",
                str(pal_file),
                "--model",
                "test-model",
                "--provider",
                "mock",
                "--vars",
                '{"user_query": "Execute test"}',
                "--json-output",
            ],
        )

        assert result.exit_code == 0
        # Should contain JSON output with execution result
        assert "response" in result.output
        assert "input_tokens" in result.output
        assert "output_tokens" in result.output

    def test_execute_with_output_file(self, sample_pal_setup):
        """Test execution with output to file."""
        temp_dir = sample_pal_setup["temp_dir"]
        pal_file = sample_pal_setup["pal_file"]
        output_file = temp_dir / "response.txt"

        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "execute",
                str(pal_file),
                "--model",
                "test-model",
                "--provider",
                "mock",
                "--vars",
                '{"user_query": "File output test"}',
                "--output",
                str(output_file),
            ],
        )

        assert result.exit_code == 0
        assert f"Response written to {output_file}" in result.output

        # Check output file
        assert output_file.exists()
        content = output_file.read_text()
        assert len(content) > 0  # Should contain the mock response

    def test_execute_missing_model(self, sample_pal_setup):
        """Test execution without required model parameter."""
        runner = CliRunner()
        pal_file = sample_pal_setup["pal_file"]

        result = runner.invoke(
            cli, ["execute", str(pal_file), "--vars", '{"user_query": "test"}']
        )

        assert result.exit_code != 0
        # Should show error about missing model parameter


class TestValidateCommand:
    """Test the validate CLI command."""

    def test_validate_single_file(self, sample_pal_setup):
        """Test validating a single PAL file."""
        runner = CliRunner()
        pal_file = sample_pal_setup["pal_file"]

        result = runner.invoke(cli, ["validate", str(pal_file)])

        assert result.exit_code == 0
        assert "Valid" in result.output
        assert "1/1 files valid" in result.output

    def test_validate_library_file(self, sample_pal_setup):
        """Test validating a PAL library file."""
        runner = CliRunner()
        lib_file = sample_pal_setup["lib_file"]

        result = runner.invoke(cli, ["validate", str(lib_file)])

        assert result.exit_code == 0
        assert "Valid" in result.output
        assert "Library" in result.output

    def test_validate_directory(self, sample_pal_setup):
        """Test validating a directory of PAL files."""
        runner = CliRunner()
        temp_dir = sample_pal_setup["temp_dir"]

        result = runner.invoke(cli, ["validate", str(temp_dir)])

        assert result.exit_code == 0
        assert "2/2 files valid" in result.output  # .pal and .pal.lib files

    def test_validate_recursive(self, sample_pal_setup):
        """Test recursive validation."""
        temp_dir = sample_pal_setup["temp_dir"]

        # Create subdirectory with PAL file
        sub_dir = temp_dir / "subdir"
        sub_dir.mkdir()

        sub_pal_content = {
            "pal_version": "1.0",
            "id": "sub-prompt",
            "version": "1.0.0",
            "description": "Subdirectory prompt",
            "composition": ["Simple prompt"],
        }

        sub_pal_file = sub_dir / "sub.pal"
        with open(sub_pal_file, "w") as f:
            yaml.dump(sub_pal_content, f)

        runner = CliRunner()
        result = runner.invoke(cli, ["validate", str(temp_dir), "--recursive"])

        assert result.exit_code == 0
        assert "3/3 files valid" in result.output  # Original 2 + subdirectory file

    def test_validate_invalid_file(self, sample_pal_setup):
        """Test validation of invalid PAL file."""
        temp_dir = sample_pal_setup["temp_dir"]

        # Create invalid PAL file
        invalid_content = {"pal_version": "1.0"}  # Missing required fields
        invalid_file = temp_dir / "invalid.pal"
        with open(invalid_file, "w") as f:
            yaml.dump(invalid_content, f)

        runner = CliRunner()
        result = runner.invoke(cli, ["validate", str(invalid_file)])

        assert result.exit_code == 1
        assert "Invalid" in result.output


class TestInfoCommand:
    """Test the info CLI command."""

    def test_info_pal_file(self, sample_pal_setup):
        """Test info command on PAL file."""
        runner = CliRunner()
        pal_file = sample_pal_setup["pal_file"]

        result = runner.invoke(cli, ["info", str(pal_file)])

        assert result.exit_code == 0
        assert "cli-test-prompt" in result.output
        assert "1.0.0" in result.output
        assert "CLI test prompt" in result.output
        assert "Test Suite" in result.output  # Author
        assert "Variables" in result.output
        assert "Imports" in result.output

    def test_info_library_file(self, sample_pal_setup):
        """Test info command on library file."""
        runner = CliRunner()
        lib_file = sample_pal_setup["lib_file"]

        result = runner.invoke(cli, ["info", str(lib_file)])

        assert result.exit_code == 0
        assert "cli.test" in result.output
        assert "CLI test library" in result.output
        assert "Components" in result.output
        assert "helpful_assistant" in result.output
        assert "json_format" in result.output


class TestEvaluateCommand:
    """Test the evaluate CLI command."""

    def test_evaluate_basic(self, sample_pal_setup):
        """Test basic evaluation command."""
        runner = CliRunner()
        eval_file = sample_pal_setup["eval_file"]
        pal_file = sample_pal_setup["pal_file"]

        result = runner.invoke(
            cli,
            [
                "evaluate",
                str(eval_file),
                "--pal-file",
                str(pal_file),
                "--model",
                "test-model",
                "--provider",
                "mock",
            ],
        )

        assert result.exit_code == 0 or result.exit_code == 1  # May fail on assertions
        assert "tests" in result.output.lower()

    def test_evaluate_json_output(self, sample_pal_setup):
        """Test evaluation with JSON output."""
        runner = CliRunner()
        eval_file = sample_pal_setup["eval_file"]
        pal_file = sample_pal_setup["pal_file"]

        result = runner.invoke(
            cli,
            [
                "evaluate",
                str(eval_file),
                "--pal-file",
                str(pal_file),
                "--model",
                "test-model",
                "--provider",
                "mock",
                "--format",
                "json",
            ],
        )

        # Should produce JSON output regardless of pass/fail
        assert "prompt_id" in result.output or result.exit_code in [0, 1]

    def test_evaluate_with_output_file(self, sample_pal_setup):
        """Test evaluation with output to file."""
        temp_dir = sample_pal_setup["temp_dir"]
        eval_file = sample_pal_setup["eval_file"]
        pal_file = sample_pal_setup["pal_file"]
        output_file = temp_dir / "eval_report.txt"

        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "evaluate",
                str(eval_file),
                "--pal-file",
                str(pal_file),
                "--model",
                "test-model",
                "--provider",
                "mock",
                "--output",
                str(output_file),
            ],
        )

        # Should write report to file
        assert output_file.exists()
        content = output_file.read_text()
        assert len(content) > 0


class TestCLIIntegration:
    """Test CLI integration scenarios."""

    def test_workflow_compile_execute_evaluate(self, sample_pal_setup):
        """Test complete workflow: compile -> execute -> evaluate."""
        runner = CliRunner()
        pal_file = sample_pal_setup["pal_file"]
        eval_file = sample_pal_setup["eval_file"]
        temp_dir = sample_pal_setup["temp_dir"]

        # Step 1: Compile
        result1 = runner.invoke(
            cli,
            [
                "compile",
                str(pal_file),
                "--vars",
                '{"user_query": "Workflow test"}',
                "--output",
                str(temp_dir / "compiled.txt"),
            ],
        )
        assert result1.exit_code == 0

        # Step 2: Execute
        result2 = runner.invoke(
            cli,
            [
                "execute",
                str(pal_file),
                "--model",
                "test-model",
                "--provider",
                "mock",
                "--vars",
                '{"user_query": "Workflow test"}',
                "--json-output",
                "--output",
                str(temp_dir / "response.json"),
            ],
        )
        assert result2.exit_code == 0

        # Step 3: Evaluate
        result3 = runner.invoke(
            cli,
            [
                "evaluate",
                str(eval_file),
                "--pal-file",
                str(pal_file),
                "--model",
                "test-model",
                "--provider",
                "mock",
                "--format",
                "json",
                "--output",
                str(temp_dir / "eval_report.json"),
            ],
        )
        # Evaluation may pass or fail, but should complete
        assert result3.exit_code in [0, 1]

        # Verify all output files exist
        assert (temp_dir / "compiled.txt").exists()
        assert (temp_dir / "response.json").exists()
        assert (temp_dir / "eval_report.json").exists()

    def test_verbose_logging(self, sample_pal_setup):
        """Test verbose logging flag."""
        runner = CliRunner()
        pal_file = sample_pal_setup["pal_file"]

        result = runner.invoke(
            cli,
            [
                "--verbose",
                "compile",
                str(pal_file),
                "--vars",
                '{"user_query": "Verbose test"}',
                "--no-format",
            ],
        )

        assert result.exit_code == 0
        # With verbose logging, should still work but may have additional output

    def test_error_handling_consistency(self, sample_pal_setup):
        """Test that CLI error handling is consistent across commands."""
        runner = CliRunner()
        nonexistent_file = sample_pal_setup["temp_dir"] / "nonexistent.pal"

        commands_with_file_arg = [
            ["compile", str(nonexistent_file)],
            ["execute", str(nonexistent_file), "--model", "test"],
            ["validate", str(nonexistent_file)],
            ["info", str(nonexistent_file)],
        ]

        for command_args in commands_with_file_arg:
            result = runner.invoke(cli, command_args)
            assert result.exit_code != 0
            # All should show error messages consistently
            assert "Error:" in result.output or result.exit_code != 0


class TestCLIErrorHandling:
    """Test CLI error handling and edge cases."""

    def test_missing_file_error(self):
        """Test handling of missing file arguments."""
        runner = CliRunner()

        result = runner.invoke(cli, ["compile", "/nonexistent/file.pal"])
        assert result.exit_code != 0

    def test_invalid_provider_error(self, sample_pal_setup):
        """Test handling of invalid provider."""
        runner = CliRunner()
        pal_file = sample_pal_setup["pal_file"]

        result = runner.invoke(
            cli,
            [
                "execute",
                str(pal_file),
                "--model",
                "test-model",
                "--provider",
                "invalid_provider",
                "--vars",
                '{"user_query": "test"}',
            ],
        )

        assert result.exit_code != 0

    def test_malformed_vars_json(self, sample_pal_setup):
        """Test handling of malformed JSON in --vars."""
        runner = CliRunner()
        pal_file = sample_pal_setup["pal_file"]

        result = runner.invoke(
            cli, ["compile", str(pal_file), "--vars", "{malformed: json"]
        )

        assert result.exit_code == 1
        assert "Invalid JSON" in result.output
