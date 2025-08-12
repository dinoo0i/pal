Loader API
==========

.. currentmodule:: pal.core.loader

The loader module provides unified file loading for all PAL file types.

Loader
------

.. autoclass:: Loader
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __init__, __aenter__, __aexit__

Supported File Types
--------------------

The loader supports three file types:

1. **Prompt Assemblies** (`.pal`) - Main prompt definitions
2. **Component Libraries** (`.pal.lib`) - Reusable components
3. **Evaluation Suites** (`.eval.yaml`) - Test configurations

Loading Methods
---------------

Each file type has both sync and async loading methods:

- :meth:`~Loader.load_prompt_assembly` /
  :meth:`~Loader.load_prompt_assembly_async`
- :meth:`~Loader.load_component_library` /
  :meth:`~Loader.load_component_library_async`
- :meth:`~Loader.load_evaluation_suite` /
  :meth:`~Loader.load_evaluation_suite_async`

Examples
--------

Basic file loading::

    from pal import Loader
    from pathlib import Path

    loader = Loader()

    # Load a prompt assembly
    assembly = loader.load_prompt_assembly("my_prompt.pal")

    # Load a component library
    library = loader.load_component_library("components.pal.lib")

    # Load evaluation suite
    evaluation = loader.load_evaluation_suite("tests.eval.yaml")

Async loading with context manager::

    async with Loader(timeout=60.0) as loader:
        assembly = await loader.load_prompt_assembly_async("prompt.pal")
        library = await loader.load_component_library_async(
            "https://example.com/libs/personas.pal.lib"
        )

Loading from URLs::

    loader = Loader(timeout=30.0)

    # Load from GitHub
    library = await loader.load_component_library_async(
        "https://raw.githubusercontent.com/org/repo/main/libs/tasks.pal.lib"
    )

    # Load from any HTTP source
    assembly = await loader.load_prompt_assembly_async(
        "https://example.com/prompts/analysis.pal"
    )

Error Handling
--------------

The loader raises specific exceptions:

- :class:`~pal.exceptions.PALLoadError` - File cannot be loaded
- :class:`~pal.exceptions.PALValidationError` - File format is invalid

Example::

    from pal import Loader
    from pal.exceptions import PALLoadError, PALValidationError

    loader = Loader()

    try:
        assembly = loader.load_prompt_assembly("invalid.pal")
    except PALLoadError as e:
        print(f"Failed to load file: {e}")
    except PALValidationError as e:
        print(f"Invalid format: {e}")
        print(f"Validation errors: {e.context['validation_errors']}")
