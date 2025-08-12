"""Comprehensive tests for PAL loader system to improve coverage."""

import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
import yaml

from pal.core.loader import Loader
from pal.exceptions.core import PALLoadError, PALValidationError


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_pal_content():
    """Sample PAL file content."""
    return {
        "pal_version": "1.0",
        "id": "test-prompt",
        "version": "1.0.0",
        "description": "Test prompt",
        "variables": [],
        "composition": ["Test content"],
    }


@pytest.fixture
def sample_lib_content():
    """Sample library file content."""
    return {
        "pal_version": "1.0",
        "library_id": "test.lib",
        "version": "1.0.0",
        "description": "Test library",
        "type": "trait",
        "components": [
            {
                "name": "test_component",
                "description": "Test component",
                "content": "Test content",
            }
        ],
    }


@pytest.fixture
def sample_eval_content():
    """Sample evaluation file content."""
    return {
        "pal_version": "1.0",
        "prompt_id": "test-prompt",
        "target_version": "1.0.0",
        "description": "Test evaluation",
        "test_cases": [
            {
                "name": "test_case",
                "description": "Test case",
                "variables": {},
                "assertions": [{"type": "length", "config": {"min_length": 1}}],
            }
        ],
    }


class TestLoaderAsyncContextManager:
    """Test async context manager functionality."""

    @pytest.mark.asyncio
    async def test_async_context_manager_enter_exit(self):
        """Test async context manager entry and exit."""
        loader = Loader()

        # Test enter
        result = await loader.__aenter__()
        assert result is loader
        assert loader._http_client is not None

        # Test exit
        await loader.__aexit__(None, None, None)

    @pytest.mark.asyncio
    async def test_async_context_manager_with_statement(self):
        """Test using loader in async with statement."""
        async with Loader() as loader:
            assert loader._http_client is not None

        # After exit, client should be closed but the instance should still exist
        assert loader._http_client is not None  # Client object exists but is closed


class TestLoaderSyncMethods:
    """Test synchronous wrapper methods."""

    def test_load_evaluation_suite_sync(self, temp_dir, sample_eval_content):
        """Test synchronous evaluation suite loading."""
        eval_file = temp_dir / "test.eval.yaml"
        with open(eval_file, "w") as f:
            yaml.dump(sample_eval_content, f)

        loader = Loader()
        evaluation_suite = loader.load_evaluation_suite(eval_file)

        assert evaluation_suite.prompt_id == "test-prompt"
        assert evaluation_suite.target_version == "1.0.0"


class TestLoaderErrorHandling:
    """Test various error handling scenarios."""

    @pytest.mark.asyncio
    async def test_load_prompt_assembly_validation_error(self, temp_dir):
        """Test validation error handling for prompt assembly."""
        # Create invalid PAL file
        invalid_content = {
            "pal_version": "1.0",
            "id": "test-prompt",
            # Missing required fields
        }

        pal_file = temp_dir / "invalid.pal"
        with open(pal_file, "w") as f:
            yaml.dump(invalid_content, f)

        loader = Loader()

        with pytest.raises(PALValidationError) as exc_info:
            await loader.load_prompt_assembly_async(pal_file)

        assert "Invalid prompt assembly format" in str(exc_info.value)
        assert "validation_errors" in exc_info.value.context

    @pytest.mark.asyncio
    async def test_load_component_library_validation_error(self, temp_dir):
        """Test validation error handling for component library."""
        invalid_content = {
            "pal_version": "1.0",
            "library_id": "test.lib",
            # Missing required fields
        }

        lib_file = temp_dir / "invalid.pal.lib"
        with open(lib_file, "w") as f:
            yaml.dump(invalid_content, f)

        loader = Loader()

        with pytest.raises(PALValidationError) as exc_info:
            await loader.load_component_library_async(lib_file)

        assert "Invalid component library format" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_load_evaluation_suite_validation_error(self, temp_dir):
        """Test validation error handling for evaluation suite."""
        invalid_content = {
            "pal_version": "1.0",
            "prompt_id": "test-prompt",
            # Missing required fields
        }

        eval_file = temp_dir / "invalid.eval.yaml"
        with open(eval_file, "w") as f:
            yaml.dump(invalid_content, f)

        loader = Loader()

        with pytest.raises(PALValidationError) as exc_info:
            await loader.load_evaluation_suite_async(eval_file)

        assert "Invalid evaluation suite format" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_load_from_url(self):
        """Test loading from URL."""
        loader = Loader()

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_response = AsyncMock()
            mock_response.text = 'pal_version: "1.0"\nid: "test"\nversion: "1.0.0"\ndescription: "test"\nvariables: []\ncomposition: ["test"]'
            mock_response.raise_for_status.return_value = None
            mock_client.get.return_value = mock_response
            mock_client_class.return_value = mock_client

            result = await loader.load_prompt_assembly_async(
                "https://example.com/test.pal"
            )

            assert result.id == "test"
            mock_client.get.assert_called_once_with("https://example.com/test.pal")

    @pytest.mark.asyncio
    async def test_load_from_url_http_error(self):
        """Test HTTP error handling when loading from URL."""
        import httpx

        loader = Loader()

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_response = AsyncMock()
            mock_response.status_code = 404
            mock_response.text = "Not Found"
            mock_error = httpx.HTTPStatusError(
                "404", request=None, response=mock_response
            )
            mock_client.get.side_effect = mock_error
            mock_client_class.return_value = mock_client

            with pytest.raises(PALLoadError) as exc_info:
                await loader.load_prompt_assembly_async(
                    "https://example.com/notfound.pal"
                )

            assert "HTTP 404 error" in str(exc_info.value)
            assert "status_code" in exc_info.value.context

    @pytest.mark.asyncio
    async def test_load_from_url_request_error(self):
        """Test network error handling when loading from URL."""
        import httpx

        loader = Loader()

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_error = httpx.RequestError("Connection failed")
            mock_client.get.side_effect = mock_error
            mock_client_class.return_value = mock_client

            with pytest.raises(PALLoadError) as exc_info:
                await loader.load_prompt_assembly_async("https://example.com/test.pal")

            assert "Network error" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_load_from_url_unexpected_error(self):
        """Test unexpected error handling when loading from URL."""
        loader = Loader()

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get.side_effect = Exception("Unexpected error")
            mock_client_class.return_value = mock_client

            with pytest.raises(PALLoadError) as exc_info:
                await loader.load_prompt_assembly_async("https://example.com/test.pal")

            assert "Unexpected error" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_load_from_file_not_found(self, temp_dir):
        """Test file not found error handling."""
        loader = Loader()
        nonexistent_file = temp_dir / "nonexistent.pal"

        with pytest.raises(PALLoadError) as exc_info:
            await loader.load_prompt_assembly_async(nonexistent_file)

        assert "File not found" in str(exc_info.value)
        assert "path" in exc_info.value.context

    @pytest.mark.asyncio
    async def test_load_from_file_permission_error(self, temp_dir, sample_pal_content):
        """Test permission error handling."""
        pal_file = temp_dir / "restricted.pal"
        with open(pal_file, "w") as f:
            yaml.dump(sample_pal_content, f)

        loader = Loader()

        # Mock permission error
        with patch(
            "asyncio.to_thread", side_effect=PermissionError("Permission denied")
        ):
            with pytest.raises(PALLoadError) as exc_info:
                await loader.load_prompt_assembly_async(pal_file)

            assert "Permission denied" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_load_from_file_generic_error(self, temp_dir, sample_pal_content):
        """Test generic file loading error handling."""
        pal_file = temp_dir / "error.pal"
        with open(pal_file, "w") as f:
            yaml.dump(sample_pal_content, f)

        loader = Loader()

        # Mock generic error
        with patch("asyncio.to_thread", side_effect=Exception("Generic error")):
            with pytest.raises(PALLoadError) as exc_info:
                await loader.load_prompt_assembly_async(pal_file)

            assert "Failed to read file" in str(exc_info.value)
            assert "error" in exc_info.value.context

    @pytest.mark.asyncio
    async def test_parse_yaml_invalid_syntax(self, temp_dir):
        """Test YAML parsing error handling."""
        # Create file with invalid YAML
        invalid_file = temp_dir / "invalid.yaml"
        with open(invalid_file, "w") as f:
            f.write("invalid: yaml: content: [")

        loader = Loader()

        with pytest.raises(PALValidationError) as exc_info:
            await loader.load_prompt_assembly_async(invalid_file)

        assert "Invalid YAML syntax" in str(exc_info.value)
        assert "yaml_error" in exc_info.value.context

    @pytest.mark.asyncio
    async def test_parse_yaml_non_dict_content(self, temp_dir):
        """Test YAML content that's not a dictionary."""
        # Create file with valid YAML but not a dict
        non_dict_file = temp_dir / "non_dict.yaml"
        with open(non_dict_file, "w") as f:
            yaml.dump(["item1", "item2"], f)

        loader = Loader()

        with pytest.raises(PALValidationError) as exc_info:
            await loader.load_prompt_assembly_async(non_dict_file)

        assert "YAML content must be a dictionary" in str(exc_info.value)
        assert "got list" in str(exc_info.value)


class TestLoaderHTTPClientManagement:
    """Test HTTP client management in URL loading."""

    @pytest.mark.asyncio
    async def test_http_client_creation_on_demand(self):
        """Test HTTP client is created on demand for URL loading."""
        loader = Loader(timeout=10.0)
        assert loader._http_client is None

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_response = AsyncMock()
            mock_response.text = 'pal_version: "1.0"\nid: "test"\nversion: "1.0.0"\ndescription: "test"\nvariables: []\ncomposition: ["test"]'
            mock_response.raise_for_status.return_value = None
            mock_client.get.return_value = mock_response
            mock_client_class.return_value = mock_client

            await loader.load_prompt_assembly_async("https://example.com/test.pal")

            # Client should be created with correct timeout
            mock_client_class.assert_called_once_with(timeout=10.0)
            assert loader._http_client is not None

    @pytest.mark.asyncio
    async def test_http_client_reuse(self):
        """Test HTTP client is reused for multiple requests."""
        loader = Loader()

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_response = AsyncMock()
            mock_response.text = 'pal_version: "1.0"\nid: "test"\nversion: "1.0.0"\ndescription: "test"\nvariables: []\ncomposition: ["test"]'
            mock_response.raise_for_status.return_value = None
            mock_client.get.return_value = mock_response
            mock_client_class.return_value = mock_client

            # First request - creates client
            await loader.load_prompt_assembly_async("https://example.com/test1.pal")

            # Second request - reuses client
            await loader.load_prompt_assembly_async("https://example.com/test2.pal")

            # Client should be created only once
            mock_client_class.assert_called_once()
            assert mock_client.get.call_count == 2


class TestLoaderInitialization:
    """Test loader initialization with different parameters."""

    def test_loader_initialization_default_timeout(self):
        """Test loader initialization with default timeout."""
        loader = Loader()
        assert loader.timeout == 30.0
        assert loader._http_client is None

    def test_loader_initialization_custom_timeout(self):
        """Test loader initialization with custom timeout."""
        loader = Loader(timeout=60.0)
        assert loader.timeout == 60.0


class TestLoaderEdgeCases:
    """Test edge cases and boundary conditions."""

    @pytest.mark.asyncio
    async def test_empty_file_handling(self, temp_dir):
        """Test handling of empty files."""
        empty_file = temp_dir / "empty.pal"
        empty_file.touch()  # Create empty file

        loader = Loader()

        with pytest.raises(PALValidationError):
            await loader.load_prompt_assembly_async(empty_file)

    @pytest.mark.asyncio
    async def test_whitespace_only_file(self, temp_dir):
        """Test handling of files with only whitespace."""
        whitespace_file = temp_dir / "whitespace.pal"
        with open(whitespace_file, "w") as f:
            f.write("   \n\t\n   ")

        loader = Loader()

        with pytest.raises(PALValidationError):
            await loader.load_prompt_assembly_async(whitespace_file)

    @pytest.mark.asyncio
    async def test_yaml_null_content(self, temp_dir):
        """Test handling of YAML files that parse to None."""
        null_file = temp_dir / "null.pal"
        with open(null_file, "w") as f:
            f.write("~")  # YAML null

        loader = Loader()

        with pytest.raises(PALValidationError) as exc_info:
            await loader.load_prompt_assembly_async(null_file)

        assert "YAML content must be a dictionary" in str(exc_info.value)
        assert "got NoneType" in str(exc_info.value)
