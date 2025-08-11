"""PAL dependency resolution and import management."""

from __future__ import annotations

from pathlib import Path

from ..exceptions.core import PALCircularDependencyError, PALResolverError
from ..models.schema import ComponentLibrary, PromptAssembly
from .loader import Loader


class ResolverCache:
    """Cache for resolved dependencies to avoid redundant loading."""

    def __init__(self) -> None:
        self._cache: dict[str, ComponentLibrary] = {}

    def get(self, path_or_url: str) -> ComponentLibrary | None:
        """Get cached library by path or URL."""
        return self._cache.get(path_or_url)

    def set(self, path_or_url: str, library: ComponentLibrary) -> None:
        """Cache a loaded library."""
        self._cache[path_or_url] = library

    def clear(self) -> None:
        """Clear the cache."""
        self._cache.clear()


class DependencyGraph:
    """Tracks dependency relationships to detect cycles."""

    def __init__(self) -> None:
        self._dependencies: dict[str, set[str]] = {}
        self._visiting: set[str] = set()
        self._visited: set[str] = set()

    def add_dependency(self, dependent: str, dependency: str) -> None:
        """Add a dependency relationship."""
        if dependent not in self._dependencies:
            self._dependencies[dependent] = set()
        self._dependencies[dependent].add(dependency)

    def check_cycles(self, start: str) -> None:
        """Check for circular dependencies using DFS."""
        self._visiting.clear()
        self._visited.clear()
        self._dfs(start, [])

    def _dfs(self, node: str, path: list[str]) -> None:
        """Depth-first search for cycle detection."""
        if node in self._visiting:
            cycle_start = path.index(node)
            cycle = " -> ".join(path[cycle_start:] + [node])
            raise PALCircularDependencyError(
                f"Circular dependency detected: {cycle}",
                context={"cycle": path[cycle_start:] + [node]},
            )

        if node in self._visited:
            return

        self._visiting.add(node)
        path.append(node)

        for dependency in self._dependencies.get(node, []):
            self._dfs(dependency, path.copy())

        self._visiting.remove(node)
        self._visited.add(node)
        path.pop()


class Resolver:
    """Resolves PAL imports and manages dependency graphs."""

    def __init__(self, loader: Loader, cache: ResolverCache | None = None) -> None:
        """Initialize resolver with a loader and optional cache."""
        self.loader = loader
        self.cache = cache or ResolverCache()
        self.dependency_graph = DependencyGraph()

    async def resolve_dependencies(
        self, prompt_assembly: PromptAssembly, base_path: Path | None = None
    ) -> dict[str, ComponentLibrary]:
        """Resolve all dependencies for a prompt assembly."""
        resolved: dict[str, ComponentLibrary] = {}

        # Reset dependency graph for this resolution
        self.dependency_graph = DependencyGraph()

        # Resolve each import
        for alias, path_or_url in prompt_assembly.imports.items():
            library = await self._resolve_single_dependency(
                path_or_url, base_path, prompt_assembly.id
            )
            resolved[alias] = library

        # Check for circular dependencies
        try:
            self.dependency_graph.check_cycles(prompt_assembly.id)
        except PALCircularDependencyError:
            raise

        return resolved

    async def _resolve_single_dependency(
        self, path_or_url: str | Path, base_path: Path | None, dependent_id: str
    ) -> ComponentLibrary:
        """Resolve a single dependency."""
        # Normalize path
        resolved_path = self._resolve_path(path_or_url, base_path)
        path_str = str(resolved_path)

        # Check cache first
        cached = self.cache.get(path_str)
        if cached:
            self.dependency_graph.add_dependency(dependent_id, cached.library_id)
            return cached

        # Load the library
        try:
            library = await self.loader.load_component_library_async(resolved_path)
        except Exception as e:
            raise PALResolverError(
                f"Failed to load dependency {path_str}: {e}",
                context={"path": path_str, "dependent": dependent_id, "error": str(e)},
            ) from e

        # Cache the library
        self.cache.set(path_str, library)

        # Add to dependency graph
        self.dependency_graph.add_dependency(dependent_id, library.library_id)

        # If this library has its own imports (for future extension)
        # we would resolve them recursively here

        return library

    def _resolve_path(
        self, path_or_url: str | Path, base_path: Path | None
    ) -> str | Path:
        """Resolve relative paths relative to base_path."""
        path_str = str(path_or_url)

        # If it's a URL, return as-is
        from urllib.parse import urlparse

        parsed = urlparse(path_str)
        if parsed.scheme in ("http", "https"):
            return path_str

        # Convert to Path for local files
        path = Path(path_str)

        # If absolute, return as-is
        if path.is_absolute():
            return path

        # If relative and we have a base path, resolve relative to it
        if base_path and not path.is_absolute():
            return base_path.parent / path

        # Otherwise return as-is (will be resolved relative to current dir)
        return path

    def validate_references(
        self,
        prompt_assembly: PromptAssembly,
        resolved_libraries: dict[str, ComponentLibrary],
    ) -> list[str]:
        """Validate that all component references in composition exist."""
        errors = []

        # Extract component references from composition
        component_refs = self._extract_component_references(prompt_assembly.composition)

        # Check each reference
        for ref in component_refs:
            if "." not in ref:
                errors.append(
                    f"Invalid component reference '{ref}': must be in format 'alias.component'"
                )
                continue

            alias, component_name = ref.split(".", 1)

            # Check if alias exists in imports
            if alias not in resolved_libraries:
                errors.append(f"Unknown import alias '{alias}' in reference '{ref}'")
                continue

            # Check if component exists in library
            library = resolved_libraries[alias]
            component_names = {comp.name for comp in library.components}
            if component_name not in component_names:
                errors.append(
                    f"Component '{component_name}' not found in library '{alias}'. "
                    f"Available components: {sorted(component_names)}"
                )

        return errors

    def _extract_component_references(self, composition: list[str]) -> set[str]:
        """Extract component references from composition strings."""
        import re

        references = set()
        # Match patterns like {{ alias.component_name }}
        pattern = r"\{\{\s*([a-zA-Z_][a-zA-Z0-9_]*\.[a-zA-Z_][a-zA-Z0-9_]*)\s*\}\}"

        # Join all composition items to analyze loop contexts
        full_composition = "\n".join(composition)

        # Find all loop variables defined in the composition
        loop_vars = set()
        for_pattern = r"\{%\s*for\s+([a-zA-Z_][a-zA-Z0-9_]*)\s+in\s+"
        loop_matches = re.findall(for_pattern, full_composition)
        loop_vars.update(loop_matches)

        for item in composition:
            matches = re.findall(pattern, item)
            for match in matches:
                alias = match.split(".")[0]

                # Skip if this is a loop variable
                if alias in loop_vars:
                    continue

                # Skip common Jinja2 variables that aren't component imports
                if alias in ["loop", "super", "self", "context"]:
                    continue

                references.add(match)

        return references

    def clear_cache(self) -> None:
        """Clear the resolver cache."""
        self.cache.clear()
