Data Models
===========

.. currentmodule:: pal.models.schema

PAL uses Pydantic models for data validation and serialization.

Core Models
-----------

PromptAssembly
~~~~~~~~~~~~~~

.. autoclass:: PromptAssembly
   :members:
   :undoc-members:
   :show-inheritance:

ComponentLibrary
~~~~~~~~~~~~~~~~

.. autoclass:: ComponentLibrary
   :members:
   :undoc-members:
   :show-inheritance:

EvaluationSuite
~~~~~~~~~~~~~~~

.. autoclass:: EvaluationSuite
   :members:
   :undoc-members:
   :show-inheritance:

ExecutionResult
~~~~~~~~~~~~~~~

.. autoclass:: ExecutionResult
   :members:
   :undoc-members:
   :show-inheritance:

Component Models
----------------

PALComponent
~~~~~~~~~~~~

.. autoclass:: PALComponent
   :members:
   :undoc-members:
   :show-inheritance:

PALVariable
~~~~~~~~~~~

.. autoclass:: PALVariable
   :members:
   :undoc-members:
   :show-inheritance:

Enums
-----

ComponentType
~~~~~~~~~~~~~

.. autoclass:: ComponentType
   :members:
   :undoc-members:
   :show-inheritance:

VariableType
~~~~~~~~~~~~

.. autoclass:: VariableType
   :members:
   :undoc-members:
   :show-inheritance:

Examples
--------

Creating a prompt assembly programmatically::

    from pal.models.schema import PromptAssembly, PALVariable, VariableType

    assembly = PromptAssembly(
        pal_version="1.0",
        id="my-prompt",
        version="1.0.0",
        description="A custom prompt",
        variables=[
            PALVariable(
                name="topic",
                type=VariableType.STRING,
                description="The topic to discuss",
                required=True
            )
        ],
        composition=[
            "Explain {{ topic }} in simple terms."
        ]
    )

Creating a component library::

    from pal.models.schema import ComponentLibrary, PALComponent, ComponentType

    library = ComponentLibrary(
        pal_version="1.0",
        library_id="my-components",
        version="1.0.0",
        description="Custom components",
        type=ComponentType.TASK,
        components=[
            PALComponent(
                name="analyze_code",
                description="Code analysis task",
                content="Analyze the following code for bugs and improvements:"
            )
        ]
    )

Working with execution results::

    from pal import PromptExecutor

    result = await executor.execute(...)

    print(f"Response: {result.response}")
    print(f"Model: {result.model}")
    print(f"Tokens: {result.metrics.total_tokens}")
    print(f"Duration: {result.metrics.execution_time_ms}ms")

    # Access raw LLM response
    print(f"Raw: {result.raw_response}")
