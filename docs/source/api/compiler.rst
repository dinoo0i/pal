Compiler API
============

.. currentmodule:: pal.core.compiler

The compiler module provides the core functionality for compiling PAL prompt
assemblies into executable prompts.

PromptCompiler
--------------

.. autoclass:: PromptCompiler
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __init__


Example Usage
-------------

Basic compilation::

    from pal import PromptCompiler
    from pathlib import Path

    compiler = PromptCompiler()

    # Synchronous compilation
    prompt = compiler.compile_from_file_sync(
        Path("my_prompt.pal"),
        variables={"topic": "Python", "level": "beginner"}
    )

    print(prompt)

Async compilation with custom loader::

    import asyncio
    from pal import PromptCompiler, Loader

    async def compile_prompt():
        loader = Loader(timeout=60.0)
        compiler = PromptCompiler(loader)

        prompt = await compiler.compile_from_file(
            Path("advanced_prompt.pal"),
            variables={"api_spec": api_data}
        )
        return prompt

    result = asyncio.run(compile_prompt())

Analyzing template variables:

.. code-block:: python

    from pal import PromptCompiler, Loader

    def analyze_variables():
        compiler = PromptCompiler()
        loader = Loader()
        assembly = loader.load_prompt_assembly("prompt.pal")

        # Find undeclared variables
        undeclared = compiler.analyze_template_variables(assembly)
        if undeclared:
            print(f"Warning: Undeclared variables: {undeclared}")

    analyze_variables()

Internal Classes
----------------

ComponentTemplateLoader
~~~~~~~~~~~~~~~~~~~~~~~

.. autoclass:: ComponentTemplateLoader
   :members:
   :show-inheritance:

This class provides custom Jinja2 template loading for PAL component
references.
