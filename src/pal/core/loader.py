"""PAL file loading and parsing functionality."""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import httpx
import yaml
from pydantic import ValidationError

from ..exceptions.core import PALLoadError, PALValidationError
from ..models.schema import ComponentLibrary, EvaluationSuite, PromptAssembly


class Loader:
    """Handles loading and parsing of PAL files from local filesystem and URLs."""

    def __init__(self, timeout: float = 30.0) -> None:
        """Initialize loader with optional timeout for HTTP requests."""
        self.timeout = timeout
        self._http_client: httpx.AsyncClient | None = None

    async def __aenter__(self) -> Loader:
        """Async context manager entry."""
        self._http_client = httpx.AsyncClient(timeout=self.timeout)
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit."""
        if self._http_client:
            await self._http_client.aclose()

    def load_prompt_assembly(self, path_or_url: str | Path) -> PromptAssembly:
        """Load and validate a .pal prompt assembly file."""
        return asyncio.run(self.load_prompt_assembly_async(path_or_url))

    def load_component_library(self, path_or_url: str | Path) -> ComponentLibrary:
        """Load and validate a .pal.lib component library file."""
        return asyncio.run(self.load_component_library_async(path_or_url))

    def load_evaluation_suite(self, path_or_url: str | Path) -> EvaluationSuite:
        """Load and validate a .eval.yaml evaluation suite file."""
        return asyncio.run(self.load_evaluation_suite_async(path_or_url))

    async def load_prompt_assembly_async(
        self, path_or_url: str | Path
    ) -> PromptAssembly:
        """Async version of load_prompt_assembly."""
        content = await self._load_content(path_or_url)
        data = self._parse_yaml(content, path_or_url)

        try:
            return PromptAssembly.model_validate(data)
        except ValidationError as e:
            raise PALValidationError(
                f"Invalid prompt assembly format in {path_or_url}",
                context={"validation_errors": e.errors(), "path": str(path_or_url)},
            ) from e

    async def load_component_library_async(
        self, path_or_url: str | Path
    ) -> ComponentLibrary:
        """Async version of load_component_library."""
        content = await self._load_content(path_or_url)
        data = self._parse_yaml(content, path_or_url)

        try:
            return ComponentLibrary.model_validate(data)
        except ValidationError as e:
            raise PALValidationError(
                f"Invalid component library format in {path_or_url}",
                context={"validation_errors": e.errors(), "path": str(path_or_url)},
            ) from e

    async def load_evaluation_suite_async(
        self, path_or_url: str | Path
    ) -> EvaluationSuite:
        """Async version of load_evaluation_suite."""
        content = await self._load_content(path_or_url)
        data = self._parse_yaml(content, path_or_url)

        try:
            return EvaluationSuite.model_validate(data)
        except ValidationError as e:
            raise PALValidationError(
                f"Invalid evaluation suite format in {path_or_url}",
                context={"validation_errors": e.errors(), "path": str(path_or_url)},
            ) from e

    async def _load_content(self, path_or_url: str | Path) -> str:
        """Load content from file path or URL."""
        path_str = str(path_or_url)

        # Check if it's a URL
        parsed = urlparse(path_str)
        if parsed.scheme in ("http", "https"):
            return await self._load_from_url(path_str)
        return await self._load_from_file(Path(path_str))

    async def _load_from_file(self, path: Path) -> str:
        """Load content from local file."""
        try:
            # Use asyncio to avoid blocking on large files
            return await asyncio.to_thread(path.read_text, encoding="utf-8")
        except FileNotFoundError as e:
            raise PALLoadError(
                f"File not found: {path}", context={"path": str(path)}
            ) from e
        except PermissionError as e:
            raise PALLoadError(
                f"Permission denied reading file: {path}", context={"path": str(path)}
            ) from e
        except Exception as e:
            raise PALLoadError(
                f"Failed to read file {path}: {e}",
                context={"path": str(path), "error": str(e)},
            ) from e

    async def _load_from_url(self, url: str) -> str:
        """Load content from URL."""
        if not self._http_client:
            self._http_client = httpx.AsyncClient(timeout=self.timeout)

        try:
            response = await self._http_client.get(url)
            response.raise_for_status()
            return response.text
        except httpx.HTTPStatusError as e:
            raise PALLoadError(
                f"HTTP {e.response.status_code} error loading {url}: {e.response.text}",
                context={"url": url, "status_code": e.response.status_code},
            ) from e
        except httpx.RequestError as e:
            raise PALLoadError(
                f"Network error loading {url}: {e}",
                context={"url": url, "error": str(e)},
            ) from e
        except Exception as e:
            raise PALLoadError(
                f"Unexpected error loading {url}: {e}",
                context={"url": url, "error": str(e)},
            ) from e

    def _parse_yaml(self, content: str, source: str | Path) -> dict[str, Any]:
        """Parse YAML content with error handling."""
        try:
            data = yaml.safe_load(content)
            if not isinstance(data, dict):
                raise PALValidationError(
                    f"YAML content must be a dictionary, got {type(data).__name__}",
                    context={"source": str(source)},
                )
            return data
        except yaml.YAMLError as e:
            raise PALValidationError(
                f"Invalid YAML syntax in {source}: {e}",
                context={"source": str(source), "yaml_error": str(e)},
            ) from e
