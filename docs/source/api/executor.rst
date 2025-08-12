Executor API
============

.. currentmodule:: pal.core.executor

The executor module handles LLM interactions and prompt execution.

PromptExecutor
--------------

.. autoclass:: PromptExecutor
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __init__

LLM Clients
-----------

MockLLMClient
~~~~~~~~~~~~~

.. autoclass:: MockLLMClient
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __init__

OpenAIClient
~~~~~~~~~~~~

.. autoclass:: OpenAIClient
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __init__

AnthropicClient
~~~~~~~~~~~~~~~

.. autoclass:: AnthropicClient
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __init__

Protocols
---------

LLMClient
~~~~~~~~~

.. autoclass:: LLMClient
   :members:
   :show-inheritance:

BaseLLMClient
~~~~~~~~~~~~~

.. autoclass:: BaseLLMClient
   :members:
   :show-inheritance:

Examples
--------

Using OpenAI::

    from pal import PromptExecutor, OpenAIClient

    client = OpenAIClient(api_key="sk-...")
    executor = PromptExecutor(client, log_file=Path("executions.jsonl"))

    result = await executor.execute(
        compiled_prompt="Analyze this data...",
        prompt_assembly=assembly,
        model="gpt-4-turbo",
        temperature=0.3,
        max_tokens=2000
    )

    print(f"Response: {result.response}")
    print(f"Tokens used: {result.metrics.total_tokens}")

Using Anthropic::

    from pal import PromptExecutor, AnthropicClient

    client = AnthropicClient()  # Uses ANTHROPIC_API_KEY env var
    executor = PromptExecutor(client)

    result = await executor.execute(
        compiled_prompt=prompt,
        prompt_assembly=assembly,
        model="claude-3-opus-20240229",
        max_tokens=4000
    )

Testing with mock client::

    from pal import PromptExecutor, MockLLMClient

    mock = MockLLMClient(response="Test response")
    executor = PromptExecutor(mock)

    result = await executor.execute(
        compiled_prompt="Test prompt",
        prompt_assembly=assembly,
        model="mock-model"
    )

    assert mock.call_count == 1
    assert mock.last_prompt == "Test prompt"
