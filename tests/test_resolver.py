"""Tests for PAL dependency resolution and import management."""

import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, Mock

import pytest
import yaml

from pal.core.loader import Loader
from pal.core.resolver import DependencyGraph, Resolver, ResolverCache
from pal.exceptions.core import PALCircularDependencyError, PALResolverError
from pal.models.schema import ComponentLibrary, PromptAssembly


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_libraries(temp_dir):
    """Create sample component libraries for testing."""
    # Library A
    lib_a_content = {
        "pal_version": "1.0",
        "library_id": "lib.a",
        "version": "1.0.0",
        "description": "Library A",
        "type": "trait",
        "components": [
            {
                "name": "component_a",
                "description": "Component from library A",
                "content": "Content from A",
            }
        ],
    }

    lib_a_file = temp_dir / "lib_a.pal.lib"
    with open(lib_a_file, "w") as f:
        yaml.dump(lib_a_content, f)

    # Library B
    lib_b_content = {
        "pal_version": "1.0",
        "library_id": "lib.b",
        "version": "1.0.0",
        "description": "Library B",
        "type": "reasoning",
        "components": [
            {
                "name": "component_b",
                "description": "Component from library B",
                "content": "Content from B",
            }
        ],
    }

    lib_b_file = temp_dir / "lib_b.pal.lib"
    with open(lib_b_file, "w") as f:
        yaml.dump(lib_b_content, f)

    return {"lib_a": lib_a_file, "lib_b": lib_b_file}


class TestResolverCache:
    """Test resolver cache functionality."""

    def test_cache_operations(self):
        """Test cache get, set, and clear operations."""
        cache = ResolverCache()

        # Test empty cache
        assert cache.get("nonexistent") is None

        # Test set and get
        mock_library = Mock(spec=ComponentLibrary)
        cache.set("test_path", mock_library)
        assert cache.get("test_path") is mock_library

        # Test clear
        cache.clear()
        assert cache.get("test_path") is None


class TestDependencyGraph:
    """Test dependency graph and cycle detection."""

    def test_simple_dependency(self):
        """Test adding simple dependencies without cycles."""
        graph = DependencyGraph()

        graph.add_dependency("A", "B")
        graph.add_dependency("B", "C")

        # Should not raise any exceptions
        graph.check_cycles("A")

    def test_circular_dependency_detection(self):
        """Test detection of circular dependencies."""
        graph = DependencyGraph()

        # Create a cycle: A -> B -> C -> A
        graph.add_dependency("A", "B")
        graph.add_dependency("B", "C")
        graph.add_dependency("C", "A")

        with pytest.raises(PALCircularDependencyError) as exc_info:
            graph.check_cycles("A")

        assert "Circular dependency detected" in str(exc_info.value)
        assert "A -> B -> C -> A" in str(exc_info.value)

    def test_self_reference_cycle(self):
        """Test detection of self-referencing cycles."""
        graph = DependencyGraph()

        graph.add_dependency("A", "A")

        with pytest.raises(PALCircularDependencyError):
            graph.check_cycles("A")

    def test_complex_dependency_graph(self):
        """Test more complex dependency graphs without cycles."""
        graph = DependencyGraph()

        # Diamond dependency: A -> B,C -> D
        graph.add_dependency("A", "B")
        graph.add_dependency("A", "C")
        graph.add_dependency("B", "D")
        graph.add_dependency("C", "D")

        # Should not raise any exceptions
        graph.check_cycles("A")


class TestResolver:
    """Test the resolver functionality."""

    @pytest.fixture
    def resolver(self):
        """Create a resolver with mocked loader."""
        loader = Mock(spec=Loader)
        return Resolver(loader)

    def test_resolve_path_absolute(self, resolver):
        """Test resolving absolute paths."""
        absolute_path = Path("/absolute/path/to/lib.pal.lib")
        result = resolver._resolve_path(absolute_path, None)
        assert result == absolute_path

    def test_resolve_path_relative(self, resolver):
        """Test resolving relative paths."""
        base_path = Path("/base/path/prompt.pal")
        relative_path = Path("../libs/lib.pal.lib")

        result = resolver._resolve_path(relative_path, base_path)
        expected = base_path.parent / relative_path
        assert result == expected

    def test_resolve_path_url(self, resolver):
        """Test handling URL paths."""
        url = "https://example.com/lib.pal.lib"
        result = resolver._resolve_path(url, None)
        assert result == url

    @pytest.mark.asyncio
    async def test_resolve_dependencies_success(self, sample_libraries):
        """Test successful dependency resolution."""
        loader = Loader()
        resolver = Resolver(loader)

        # Create a prompt assembly with imports
        assembly = PromptAssembly(
            pal_version="1.0",
            id="test-prompt",
            version="1.0.0",
            description="Test prompt",
            imports={
                "lib_a": str(sample_libraries["lib_a"]),
                "lib_b": str(sample_libraries["lib_b"]),
            },
            composition=["{{ lib_a.component_a }}", "{{ lib_b.component_b }}"],
        )

        resolved = await resolver.resolve_dependencies(assembly)

        assert len(resolved) == 2
        assert "lib_a" in resolved
        assert "lib_b" in resolved
        assert resolved["lib_a"].library_id == "lib.a"
        assert resolved["lib_b"].library_id == "lib.b"

    @pytest.mark.asyncio
    async def test_resolve_dependencies_missing_file(self, temp_dir):
        """Test error handling for missing dependency files."""
        loader = Loader()
        resolver = Resolver(loader)

        assembly = PromptAssembly(
            pal_version="1.0",
            id="test-prompt",
            version="1.0.0",
            description="Test prompt",
            imports={"missing": str(temp_dir / "missing.pal.lib")},
            composition=["{{ missing.component }}"],
        )

        with pytest.raises(PALResolverError) as exc_info:
            await resolver.resolve_dependencies(assembly)

        assert "Failed to load dependency" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_cache_usage(self, sample_libraries):
        """Test that resolver uses cache properly."""
        loader = Loader()
        cache = ResolverCache()
        resolver = Resolver(loader, cache)

        assembly = PromptAssembly(
            pal_version="1.0",
            id="test-prompt",
            version="1.0.0",
            description="Test prompt",
            imports={"lib_a": str(sample_libraries["lib_a"])},
            composition=["{{ lib_a.component_a }}"],
        )

        # First resolution should load from file
        resolved1 = await resolver.resolve_dependencies(assembly)

        # Second resolution should use cache
        resolved2 = await resolver.resolve_dependencies(assembly)

        assert resolved1["lib_a"] is resolved2["lib_a"]  # Same object from cache


class TestReferenceValidation:
    """Test component reference validation."""

    def test_extract_component_references(self):
        """Test extraction of component references from composition."""
        resolver = Resolver(Mock())

        composition = [
            "{{ lib1.component1 }}",
            "Some text {{ lib2.component2 }} more text",
            "{{ lib1.another_component }}",
            "Plain text without references",
        ]

        refs = resolver._extract_component_references(composition)

        expected = {"lib1.component1", "lib2.component2", "lib1.another_component"}
        assert refs == expected

    def test_extract_references_with_loops(self):
        """Test extraction that ignores Jinja loop variables."""
        resolver = Resolver(Mock())

        composition = [
            "{% for item in items %}",
            "{{ item.value }}",  # This should be ignored as 'item' is a loop variable
            "{% endfor %}",
            "{{ lib.component }}",  # This should be included
        ]

        refs = resolver._extract_component_references(composition)

        # Should only include lib.component, not item.value
        assert refs == {"lib.component"}

    def test_validate_references_success(self, sample_libraries):
        """Test successful reference validation."""
        loader = Loader()
        resolver = Resolver(loader)

        # Load libraries
        lib_a = loader.load_component_library(sample_libraries["lib_a"])
        lib_b = loader.load_component_library(sample_libraries["lib_b"])
        resolved_libraries = {"lib_a": lib_a, "lib_b": lib_b}

        assembly = PromptAssembly(
            pal_version="1.0",
            id="test-prompt",
            version="1.0.0",
            description="Test prompt",
            imports={
                "lib_a": str(sample_libraries["lib_a"]),
                "lib_b": str(sample_libraries["lib_b"]),
            },
            composition=["{{ lib_a.component_a }}", "{{ lib_b.component_b }}"],
        )

        errors = resolver.validate_references(assembly, resolved_libraries)
        assert len(errors) == 0

    def test_validate_references_missing_component(self, sample_libraries):
        """Test validation with missing component references."""
        loader = Loader()
        resolver = Resolver(loader)

        lib_a = loader.load_component_library(sample_libraries["lib_a"])
        resolved_libraries = {"lib_a": lib_a}

        assembly = PromptAssembly(
            pal_version="1.0",
            id="test-prompt",
            version="1.0.0",
            description="Test prompt",
            imports={"lib_a": str(sample_libraries["lib_a"])},
            composition=["{{ lib_a.nonexistent_component }}"],
        )

        errors = resolver.validate_references(assembly, resolved_libraries)
        assert len(errors) == 1
        assert "Component 'nonexistent_component' not found" in errors[0]

    def test_validate_references_unknown_alias(self, sample_libraries):
        """Test validation with unknown import alias."""
        loader = Loader()
        resolver = Resolver(loader)

        lib_a = loader.load_component_library(sample_libraries["lib_a"])
        resolved_libraries = {"lib_a": lib_a}

        assembly = PromptAssembly(
            pal_version="1.0",
            id="test-prompt",
            version="1.0.0",
            description="Test prompt",
            imports={"lib_a": str(sample_libraries["lib_a"])},
            composition=["{{ unknown_lib.component }}"],
        )

        errors = resolver.validate_references(assembly, resolved_libraries)
        assert len(errors) == 1
        assert "Unknown import alias 'unknown_lib'" in errors[0]
