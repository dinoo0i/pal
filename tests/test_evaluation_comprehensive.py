"""Comprehensive tests for PAL evaluation system to improve coverage."""

import tempfile
from pathlib import Path

import pytest
import yaml

from pal.core.compiler import PromptCompiler
from pal.core.evaluation import (
    AssertionResult,
    ContainsAssertion,
    EvaluationReporter,
    EvaluationRunner,
    JSONFieldEqualsAssertion,
    JSONValidAssertion,
    LengthAssertion,
    RegexMatchAssertion,
    TestCaseResult,
)
from pal.core.executor import MockLLMClient, PromptExecutor
from pal.core.loader import Loader
from pal.exceptions.core import PALError
from pal.models.schema import EvaluationTestCase, ExecutionResult


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def evaluation_components():
    """Create evaluation system components."""
    loader = Loader()
    compiler = PromptCompiler(loader)
    llm_client = MockLLMClient("Mock response")
    executor = PromptExecutor(llm_client)
    runner = EvaluationRunner(loader, compiler, executor)
    reporter = EvaluationReporter()
    return {
        "loader": loader,
        "compiler": compiler,
        "executor": executor,
        "runner": runner,
        "reporter": reporter,
    }


class TestContainsAssertion:
    """Test ContainsAssertion with various configurations."""

    def test_contains_assertion_success(self):
        """Test successful contains assertion."""
        assertion = ContainsAssertion()
        result = assertion.evaluate(
            "Hello world", {"text": "world", "case_sensitive": True}
        )

        assert result.passed
        assert result.assertion_type == "contains"
        assert "contains" in result.message
        assert result.expected == "world"

    def test_contains_assertion_failure(self):
        """Test failing contains assertion."""
        assertion = ContainsAssertion()
        result = assertion.evaluate(
            "Hello world", {"text": "goodbye", "case_sensitive": True}
        )

        assert not result.passed
        assert "does not contain" in result.message

    def test_contains_assertion_case_insensitive(self):
        """Test case-insensitive contains assertion."""
        assertion = ContainsAssertion()
        result = assertion.evaluate(
            "Hello WORLD", {"text": "world", "case_sensitive": False}
        )

        assert result.passed

    def test_contains_assertion_missing_text_parameter(self):
        """Test contains assertion with missing text parameter."""
        assertion = ContainsAssertion()
        result = assertion.evaluate("Hello world", {})

        assert not result.passed
        assert "Missing 'text' parameter" in result.message

    def test_contains_assertion_empty_text(self):
        """Test contains assertion with empty text parameter."""
        assertion = ContainsAssertion()
        result = assertion.evaluate("Hello world", {"text": ""})

        assert not result.passed
        assert "Missing 'text' parameter" in result.message


class TestRegexMatchAssertion:
    """Test RegexMatchAssertion with various configurations."""

    def test_regex_match_assertion_success(self):
        """Test successful regex match assertion."""
        assertion = RegexMatchAssertion()
        result = assertion.evaluate("Hello123", {"pattern": r"\d+"})

        assert result.passed
        assert result.assertion_type == "regex_match"
        assert "matches" in result.message
        assert result.metadata["match"] == "123"

    def test_regex_match_assertion_failure(self):
        """Test failing regex match assertion."""
        assertion = RegexMatchAssertion()
        result = assertion.evaluate("Hello world", {"pattern": r"\d+"})

        assert not result.passed
        assert "does not match" in result.message
        assert result.metadata["match"] is None

    def test_regex_match_assertion_missing_pattern(self):
        """Test regex match assertion with missing pattern."""
        assertion = RegexMatchAssertion()
        result = assertion.evaluate("Hello world", {})

        assert not result.passed
        assert "Missing 'pattern' parameter" in result.message

    def test_regex_match_assertion_empty_pattern(self):
        """Test regex match assertion with empty pattern."""
        assertion = RegexMatchAssertion()
        result = assertion.evaluate("Hello world", {"pattern": ""})

        assert not result.passed
        assert "Missing 'pattern' parameter" in result.message

    def test_regex_match_assertion_invalid_regex(self):
        """Test regex match assertion with invalid regex pattern."""
        assertion = RegexMatchAssertion()
        result = assertion.evaluate("Hello world", {"pattern": "[invalid"})

        assert not result.passed
        assert "Invalid regex pattern" in result.message

    def test_regex_match_assertion_with_flags(self):
        """Test regex match assertion with flags."""
        import re

        assertion = RegexMatchAssertion()
        result = assertion.evaluate(
            "HELLO", {"pattern": "hello", "flags": re.IGNORECASE}
        )

        assert result.passed


class TestJSONValidAssertion:
    """Test JSONValidAssertion with various inputs."""

    def test_json_valid_assertion_success(self):
        """Test valid JSON assertion."""
        assertion = JSONValidAssertion()
        result = assertion.evaluate('{"key": "value"}', {})

        assert result.passed
        assert result.assertion_type == "json_valid"
        assert "valid JSON" in result.message
        assert result.metadata["parsed"] == {"key": "value"}

    def test_json_valid_assertion_with_whitespace(self):
        """Test valid JSON assertion with leading/trailing whitespace."""
        assertion = JSONValidAssertion()
        result = assertion.evaluate('  {"key": "value"}  ', {})

        assert result.passed

    def test_json_valid_assertion_failure(self):
        """Test invalid JSON assertion."""
        assertion = JSONValidAssertion()
        result = assertion.evaluate("{invalid: json}", {})

        assert not result.passed
        assert "not valid JSON" in result.message


class TestJSONFieldEqualsAssertion:
    """Test JSONFieldEqualsAssertion with various configurations."""

    def test_json_field_equals_assertion_success(self):
        """Test successful JSON field equals assertion."""
        assertion = JSONFieldEqualsAssertion()
        result = assertion.evaluate(
            '{"key": "value"}', {"path": "$.key", "value": "value"}
        )

        assert result.passed
        assert result.assertion_type == "json_field_equals"
        assert result.expected == "value"
        assert result.actual == "value"

    def test_json_field_equals_assertion_failure(self):
        """Test failing JSON field equals assertion."""
        assertion = JSONFieldEqualsAssertion()
        result = assertion.evaluate(
            '{"key": "value"}', {"path": "$.key", "value": "different"}
        )

        assert not result.passed
        assert "does not equal" in result.message

    def test_json_field_equals_assertion_missing_path(self):
        """Test JSON field equals assertion with missing path."""
        assertion = JSONFieldEqualsAssertion()
        result = assertion.evaluate('{"key": "value"}', {"value": "test"})

        assert not result.passed
        assert "Missing 'path' parameter" in result.message

    def test_json_field_equals_assertion_empty_path(self):
        """Test JSON field equals assertion with empty path."""
        assertion = JSONFieldEqualsAssertion()
        result = assertion.evaluate('{"key": "value"}', {"path": "", "value": "test"})

        assert not result.passed
        assert "Missing 'path' parameter" in result.message

    def test_json_field_equals_assertion_invalid_json(self):
        """Test JSON field equals assertion with invalid JSON."""
        assertion = JSONFieldEqualsAssertion()
        result = assertion.evaluate(
            "{invalid json}", {"path": "$.key", "value": "test"}
        )

        assert not result.passed
        assert "not valid JSON" in result.message

    def test_json_field_equals_assertion_nonexistent_path(self):
        """Test JSON field equals assertion with nonexistent path."""
        assertion = JSONFieldEqualsAssertion()
        result = assertion.evaluate(
            '{"key": "value"}', {"path": "$.nonexistent", "value": "test"}
        )

        assert not result.passed
        assert "Cannot extract path" in result.message

    def test_json_field_equals_assertion_array_access(self):
        """Test JSON field equals assertion with array access."""
        assertion = JSONFieldEqualsAssertion()
        result = assertion.evaluate(
            '{"items": ["a", "b", "c"]}', {"path": "$.items[1]", "value": "b"}
        )

        assert result.passed

    def test_json_field_equals_assertion_nested_path(self):
        """Test JSON field equals assertion with nested path."""
        assertion = JSONFieldEqualsAssertion()
        result = assertion.evaluate(
            '{"user": {"name": "John"}}', {"path": "$.user.name", "value": "John"}
        )

        assert result.passed

    def test_json_field_equals_assertion_invalid_array_index(self):
        """Test JSON field equals assertion with invalid array index."""
        assertion = JSONFieldEqualsAssertion()
        result = assertion.evaluate(
            '{"items": ["a"]}', {"path": "$.items[5]", "value": "test"}
        )

        assert not result.passed
        assert "Cannot extract path" in result.message


class TestLengthAssertion:
    """Test LengthAssertion with various configurations."""

    def test_length_assertion_exact_success(self):
        """Test successful exact length assertion."""
        assertion = LengthAssertion()
        result = assertion.evaluate("hello", {"exact_length": 5})

        assert result.passed
        assert "expected exactly 5" in result.message
        assert result.actual == 5

    def test_length_assertion_exact_failure(self):
        """Test failing exact length assertion."""
        assertion = LengthAssertion()
        result = assertion.evaluate("hello", {"exact_length": 10})

        assert not result.passed

    def test_length_assertion_min_max_success(self):
        """Test successful min/max length assertion."""
        assertion = LengthAssertion()
        result = assertion.evaluate("hello", {"min_length": 3, "max_length": 10})

        assert result.passed
        assert "between 3 and 10" in result.message

    def test_length_assertion_min_max_failure(self):
        """Test failing min/max length assertion."""
        assertion = LengthAssertion()
        result = assertion.evaluate("hi", {"min_length": 5, "max_length": 10})

        assert not result.passed

    def test_length_assertion_min_only_success(self):
        """Test successful min-only length assertion."""
        assertion = LengthAssertion()
        result = assertion.evaluate("hello world", {"min_length": 5})

        assert result.passed
        assert "at least 5" in result.message

    def test_length_assertion_min_only_failure(self):
        """Test failing min-only length assertion."""
        assertion = LengthAssertion()
        result = assertion.evaluate("hi", {"min_length": 5})

        assert not result.passed

    def test_length_assertion_max_only_success(self):
        """Test successful max-only length assertion."""
        assertion = LengthAssertion()
        result = assertion.evaluate("hi", {"max_length": 5})

        assert result.passed
        assert "at most 5" in result.message

    def test_length_assertion_max_only_failure(self):
        """Test failing max-only length assertion."""
        assertion = LengthAssertion()
        result = assertion.evaluate("hello world", {"max_length": 5})

        assert not result.passed

    def test_length_assertion_no_constraints(self):
        """Test length assertion with no constraints specified."""
        assertion = LengthAssertion()
        result = assertion.evaluate("hello", {})

        assert not result.passed
        assert "No length constraints specified" in result.message


class TestEvaluationRunner:
    """Test EvaluationRunner with various scenarios."""

    @pytest.mark.asyncio
    async def test_evaluation_runner_register_assertion(self, evaluation_components):
        """Test registering custom assertion."""
        runner = evaluation_components["runner"]
        custom_assertion = ContainsAssertion()

        runner.register_assertion("custom", custom_assertion)
        assert "custom" in runner.assertions
        assert runner.assertions["custom"] == custom_assertion

    @pytest.mark.asyncio
    async def test_evaluation_with_version_mismatch(
        self, temp_dir, evaluation_components
    ):
        """Test evaluation with version mismatch warning."""
        # Create PAL file with different version
        pal_content = {
            "pal_version": "1.0",
            "id": "test-prompt",
            "version": "2.0.0",  # Different version
            "description": "Test prompt",
            "variables": [
                {"name": "input", "type": "string", "description": "User input"}
            ],
            "composition": ["User says: {{ input }}"],
        }
        pal_file = temp_dir / "test.pal"
        with open(pal_file, "w") as f:
            yaml.dump(pal_content, f)

        # Create eval file expecting version 1.0.0
        eval_content = {
            "pal_version": "1.0",
            "prompt_id": "test-prompt",
            "target_version": "1.0.0",
            "description": "Test evaluation",
            "test_cases": [
                {
                    "name": "basic_test",
                    "description": "Basic test",
                    "variables": {"input": "Hello"},
                    "assertions": [{"type": "length", "config": {"min_length": 1}}],
                }
            ],
        }
        eval_file = temp_dir / "test.eval.yaml"
        with open(eval_file, "w") as f:
            yaml.dump(eval_content, f)

        runner = evaluation_components["runner"]
        result = await runner.run_evaluation(eval_file, pal_file, "test-model")

        # Should still work but with warning
        assert result is not None

    @pytest.mark.asyncio
    async def test_evaluation_unknown_assertion_type(
        self, temp_dir, evaluation_components
    ):
        """Test evaluation with unknown assertion type."""
        # Create PAL file
        pal_content = {
            "pal_version": "1.0",
            "id": "test-prompt",
            "version": "1.0.0",
            "description": "Test prompt",
            "variables": [
                {"name": "input", "type": "string", "description": "User input"}
            ],
            "composition": ["User says: {{ input }}"],
        }
        pal_file = temp_dir / "test.pal"
        with open(pal_file, "w") as f:
            yaml.dump(pal_content, f)

        # Create eval file with unknown assertion type
        eval_content = {
            "pal_version": "1.0",
            "prompt_id": "test-prompt",
            "target_version": "1.0.0",
            "description": "Test evaluation",
            "test_cases": [
                {
                    "name": "unknown_assertion_test",
                    "description": "Test with unknown assertion",
                    "variables": {"input": "Hello"},
                    "assertions": [{"type": "unknown_type", "config": {}}],
                }
            ],
        }
        eval_file = temp_dir / "test.eval.yaml"
        with open(eval_file, "w") as f:
            yaml.dump(eval_content, f)

        runner = evaluation_components["runner"]
        result = await runner.run_evaluation(eval_file, pal_file, "test-model")

        assert result is not None
        assert len(result.test_results) == 1
        test_result = result.test_results[0]
        assert not test_result.passed
        assertion_result = test_result.assertion_results[0]
        assert "Unknown assertion type" in assertion_result.message

    @pytest.mark.asyncio
    async def test_evaluation_find_prompt_assembly_by_id(
        self, temp_dir, evaluation_components
    ):
        """Test finding prompt assembly by ID without explicit path."""
        # Create PAL file
        pal_content = {
            "pal_version": "1.0",
            "id": "find-me-prompt",
            "version": "1.0.0",
            "description": "Test prompt",
            "variables": [
                {"name": "input", "type": "string", "description": "User input"}
            ],
            "composition": ["User says: {{ input }}"],
        }
        pal_file = temp_dir / "findme.pal"
        with open(pal_file, "w") as f:
            yaml.dump(pal_content, f)

        # Create eval file that references the prompt by ID
        eval_content = {
            "pal_version": "1.0",
            "prompt_id": "find-me-prompt",
            "target_version": "1.0.0",
            "description": "Test evaluation",
            "test_cases": [
                {
                    "name": "basic_test",
                    "description": "Basic test",
                    "variables": {"input": "Hello"},
                    "assertions": [{"type": "length", "config": {"min_length": 1}}],
                }
            ],
        }
        eval_file = temp_dir / "test.eval.yaml"
        with open(eval_file, "w") as f:
            yaml.dump(eval_content, f)

        runner = evaluation_components["runner"]
        # Don't provide pal_file parameter - should find it by ID
        result = await runner.run_evaluation(eval_file, model="test-model")

        assert result is not None

    @pytest.mark.asyncio
    async def test_evaluation_prompt_assembly_not_found(
        self, temp_dir, evaluation_components
    ):
        """Test evaluation when prompt assembly cannot be found."""
        # Create eval file with non-existent prompt ID
        eval_content = {
            "pal_version": "1.0",
            "prompt_id": "nonexistent-prompt",
            "target_version": "1.0.0",
            "description": "Test evaluation",
            "test_cases": [
                {
                    "name": "basic_test",
                    "description": "Basic test",
                    "variables": {"input": "Hello"},
                    "assertions": [{"type": "length", "config": {"min_length": 1}}],
                }
            ],
        }
        eval_file = temp_dir / "test.eval.yaml"
        with open(eval_file, "w") as f:
            yaml.dump(eval_content, f)

        runner = evaluation_components["runner"]

        with pytest.raises(PALError) as exc_info:
            await runner.run_evaluation(eval_file, model="test-model")

        assert "Could not find prompt assembly" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_test_case_execution_error(self, temp_dir, evaluation_components):
        """Test handling of test case execution errors."""
        # Create PAL file with missing required variable
        pal_content = {
            "pal_version": "1.0",
            "id": "error-prompt",
            "version": "1.0.0",
            "description": "Test prompt",
            "variables": [
                {
                    "name": "required_var",
                    "type": "string",
                    "description": "Required",
                    "required": True,
                }
            ],
            "composition": ["User says: {{ required_var }}"],
        }
        pal_file = temp_dir / "error.pal"
        with open(pal_file, "w") as f:
            yaml.dump(pal_content, f)

        # Create eval file without providing required variable
        eval_content = {
            "pal_version": "1.0",
            "prompt_id": "error-prompt",
            "target_version": "1.0.0",
            "description": "Test evaluation",
            "test_cases": [
                {
                    "name": "error_test",
                    "description": "Test that causes error",
                    "variables": {},  # Missing required_var
                    "assertions": [{"type": "length", "config": {"min_length": 1}}],
                }
            ],
        }
        eval_file = temp_dir / "test.eval.yaml"
        with open(eval_file, "w") as f:
            yaml.dump(eval_content, f)

        runner = evaluation_components["runner"]
        result = await runner.run_evaluation(eval_file, pal_file, "test-model")

        assert result is not None
        assert len(result.test_results) == 1
        test_result = result.test_results[0]
        assert not test_result.passed
        assert test_result.error is not None


class TestEvaluationReporter:
    """Test EvaluationReporter with various scenarios."""

    def test_console_report_generation(self, evaluation_components):
        """Test console report generation."""
        from pal.models.schema import (
            EvaluationAssertion,
            EvaluationSuite,
        )

        # Create mock evaluation result
        test_case = EvaluationTestCase(
            name="test_case_1",
            description="Test case",
            variables={"input": "test"},
            assertions=[EvaluationAssertion(type="length", config={"min_length": 1})],
        )

        execution_result = ExecutionResult(
            prompt_id="test-prompt",
            prompt_version="1.0.0",
            model="test-model",
            compiled_prompt="Test compiled prompt",
            response="Test response",
            metadata={},
            execution_time_ms=500.0,
            input_tokens=10,
            output_tokens=20,
            timestamp="2024-01-01T00:00:00Z",
        )

        assertion_result = AssertionResult("length", True, "Length is acceptable")
        test_result = TestCaseResult(test_case, execution_result, [assertion_result])

        evaluation_suite = EvaluationSuite(
            prompt_id="test-prompt",
            target_version="1.0.0",
            description="Test suite",
            test_cases=[test_case],
        )

        from pal.core.evaluation import EvaluationResult

        eval_result = EvaluationResult(evaluation_suite, [test_result])

        reporter = evaluation_components["reporter"]
        report = reporter.generate_console_report(eval_result)

        assert "test-prompt" in report
        assert "Total Tests: 1" in report
        assert "Passed: 1" in report
        assert "Failed: 0" in report
        assert "test_case_1" in report
        assert "✓" in report

    def test_console_report_with_errors(self, evaluation_components):
        """Test console report generation with errors."""
        from pal.models.schema import (
            EvaluationAssertion,
            EvaluationSuite,
        )

        test_case = EvaluationTestCase(
            name="error_test",
            description="Test with error",
            variables={"input": "test"},
            assertions=[EvaluationAssertion(type="length", config={"min_length": 1})],
        )

        test_result = TestCaseResult(test_case, error="Test execution failed")

        evaluation_suite = EvaluationSuite(
            prompt_id="test-prompt",
            target_version="1.0.0",
            description="Test suite",
            test_cases=[test_case],
        )

        from pal.core.evaluation import EvaluationResult

        eval_result = EvaluationResult(evaluation_suite, [test_result])

        reporter = evaluation_components["reporter"]
        report = reporter.generate_console_report(eval_result)

        assert "Error: Test execution failed" in report
        assert "✗" in report

    def test_json_report_generation(self, evaluation_components):
        """Test JSON report generation."""
        from pal.models.schema import (
            EvaluationAssertion,
            EvaluationSuite,
        )

        test_case = EvaluationTestCase(
            name="json_test",
            description="JSON test case",
            variables={"input": "test"},
            assertions=[EvaluationAssertion(type="length", config={"min_length": 1})],
        )

        execution_result = ExecutionResult(
            prompt_id="test-prompt",
            prompt_version="1.0.0",
            model="test-model",
            compiled_prompt="Test compiled prompt",
            response="Test response",
            metadata={},
            execution_time_ms=500.0,
            input_tokens=10,
            output_tokens=20,
            timestamp="2024-01-01T00:00:00Z",
        )

        assertion_result = AssertionResult("length", True, "Length is acceptable")
        test_result = TestCaseResult(test_case, execution_result, [assertion_result])

        evaluation_suite = EvaluationSuite(
            prompt_id="test-prompt",
            target_version="1.0.0",
            description="Test suite",
            test_cases=[test_case],
        )

        from pal.core.evaluation import EvaluationResult

        eval_result = EvaluationResult(evaluation_suite, [test_result])

        reporter = evaluation_components["reporter"]
        report = reporter.generate_json_report(eval_result)

        assert isinstance(report, dict)
        assert "evaluation_suite" in report
        assert "summary" in report
        assert "test_results" in report
        assert report["summary"]["total_tests"] == 1
        assert report["summary"]["passed_tests"] == 1
        assert report["summary"]["failed_tests"] == 0

    def test_json_report_with_no_execution_result(self, evaluation_components):
        """Test JSON report generation when execution result is None."""
        from pal.models.schema import (
            EvaluationAssertion,
            EvaluationSuite,
        )

        test_case = EvaluationTestCase(
            name="no_exec_test",
            description="Test with no execution result",
            variables={"input": "test"},
            assertions=[EvaluationAssertion(type="length", config={"min_length": 1})],
        )

        # Create test result without execution result
        test_result = TestCaseResult(
            test_case, execution_result=None, error="Execution failed"
        )

        evaluation_suite = EvaluationSuite(
            prompt_id="test-prompt",
            target_version="1.0.0",
            description="Test suite",
            test_cases=[test_case],
        )

        from pal.core.evaluation import EvaluationResult

        eval_result = EvaluationResult(evaluation_suite, [test_result])

        reporter = evaluation_components["reporter"]
        report = reporter.generate_json_report(eval_result)

        assert report["test_results"][0]["execution_result"] is None
        assert report["test_results"][0]["error"] == "Execution failed"
