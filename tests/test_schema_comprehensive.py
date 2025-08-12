"""Comprehensive tests for PAL schema models to improve coverage."""

import pytest
from pydantic import ValidationError

from pal.models.schema import (
    ComponentLibrary,
    EvaluationSuite,
    PALComponent,
    PALVariable,
    PromptAssembly,
)


class TestSchemaValidationCoverage:
    """Test schema validation to improve coverage of validation methods."""

    def test_variable_name_validator_coverage(self):
        """Test coverage of PALVariable.validate_name method."""
        # Create a PALVariable to trigger the validator
        var = PALVariable(
            name="valid_name", type="string", description="Valid variable"
        )
        assert var.name == "valid_name"

        # Test the validator directly
        validated_name = PALVariable.validate_name("another_valid_name")
        assert validated_name == "another_valid_name"

    def test_component_name_validator_coverage(self):
        """Test coverage of PALComponent.validate_name method."""
        # Create a PALComponent to trigger the validator
        comp = PALComponent(
            name="valid_component",
            description="Valid component",
            content="Component content",
        )
        assert comp.name == "valid_component"

        # Test the validator directly
        validated_name = PALComponent.validate_name("another_valid_component")
        assert validated_name == "another_valid_component"


class TestPromptAssemblyValidation:
    """Test PromptAssembly validation edge cases."""

    def test_imports_validation_invalid_alias(self):
        """Test imports validation with invalid alias names."""
        with pytest.raises(ValidationError) as exc_info:
            PromptAssembly(
                id="test-prompt",
                version="1.0.0",
                description="Test prompt",
                imports={"123invalid": "test.pal.lib"},  # Invalid alias
                composition=["Test composition"],
            )

        assert "Import alias '123invalid' is not a valid identifier" in str(
            exc_info.value
        )

    def test_imports_validation_invalid_extension(self):
        """Test imports validation with invalid file extensions."""
        with pytest.raises(ValidationError) as exc_info:
            PromptAssembly(
                id="test-prompt",
                version="1.0.0",
                description="Test prompt",
                imports={"mylib": "invalid.txt"},  # Invalid extension
                composition=["Test composition"],
            )

        assert "Import path 'invalid.txt' must end with .pal.lib or .pal" in str(
            exc_info.value
        )

    def test_variables_validation_duplicate_names(self):
        """Test variables validation with duplicate variable names."""
        with pytest.raises(ValidationError) as exc_info:
            PromptAssembly(
                id="test-prompt",
                version="1.0.0",
                description="Test prompt",
                variables=[
                    PALVariable(name="duplicate", type="string", description="First"),
                    PALVariable(name="duplicate", type="integer", description="Second"),
                ],
                composition=["Test composition"],
            )

        assert "Duplicate variable names found" in str(exc_info.value)


class TestComponentLibraryValidation:
    """Test ComponentLibrary validation edge cases."""

    def test_components_validation_duplicate_names(self):
        """Test components validation with duplicate component names."""
        with pytest.raises(ValidationError) as exc_info:
            ComponentLibrary(
                library_id="test.lib",
                version="1.0.0",
                description="Test library",
                type="trait",
                components=[
                    PALComponent(
                        name="duplicate", description="First", content="Content 1"
                    ),
                    PALComponent(
                        name="duplicate", description="Second", content="Content 2"
                    ),
                ],
            )

        assert "Duplicate component names found" in str(exc_info.value)


class TestEvaluationSuiteValidation:
    """Test EvaluationSuite validation edge cases."""

    def test_test_cases_validation_duplicate_names(self):
        """Test test cases validation with duplicate test case names."""
        from pal.models.schema import EvaluationAssertion, EvaluationTestCase

        with pytest.raises(ValidationError) as exc_info:
            EvaluationSuite(
                prompt_id="test-prompt",
                target_version="1.0.0",
                description="Test evaluation",
                test_cases=[
                    EvaluationTestCase(
                        name="duplicate_test",
                        description="First test",
                        variables={},
                        assertions=[
                            EvaluationAssertion(type="length", config={"min_length": 1})
                        ],
                    ),
                    EvaluationTestCase(
                        name="duplicate_test",
                        description="Second test",
                        variables={},
                        assertions=[
                            EvaluationAssertion(
                                type="contains", config={"text": "test"}
                            )
                        ],
                    ),
                ],
            )

        assert "Duplicate test case names found" in str(exc_info.value)
