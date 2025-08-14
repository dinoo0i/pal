PAL Framework Documentation
===========================

**PAL (Prompt Assembly Language)** is a framework for managing LLM prompts as
versioned, composable software artifacts.

.. toctree::
   :maxdepth: 2
   :caption: Getting Started

   quickstart

.. toctree::
   :maxdepth: 2
   :caption: User Guide

   guides/writing-prompts
   guides/component-libraries
   guides/evaluation

.. toctree::
   :maxdepth: 2
   :caption: API Reference

   api/compiler
   api/executor
   api/loader
   api/models
   api/exceptions


Quick Start
-----------

Install PAL::

    pip install pal-framework

Create your first prompt::

    from pal import PromptCompiler, PromptExecutor, AnthropicClient

    compiler = PromptCompiler()
    client = AnthropicClient()
    executor = PromptExecutor(client)

    # Compile and execute
    prompt = await compiler.compile_from_file("my_prompt.pal")
    result = await executor.execute(prompt, assembly, model="claude-3-opus")

Key Features
------------

* **Versioned Prompts**: Manage prompts like code with semantic versioning
* **Component Libraries**: Create reusable prompt components
* **Type-Safe Variables**: Define and validate prompt variables with Pydantic
* **LLM Agnostic**: Works with OpenAI, Anthropic, and custom providers
* **Evaluation Framework**: Test prompts with automated evaluation
  suites
* **Jinja2 Templating**: Full templating power with loops, conditions, and
  filters

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
