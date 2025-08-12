# Quick Start Guide

This guide will help you get started with PAL in 5 minutes.

## Installation

```bash
pip install pal-framework

# For OpenAI support
pip install "pal-framework[openai]"

# For Anthropic support  
pip install "pal-framework[anthropic]"

# For all providers
pip install "pal-framework[all]"
```

## Your First PAL Prompt

Create a file named `hello.pal`:

```yaml
pal_version: "1.0"
id: "hello-world"
version: "1.0.0"
description: "A simple greeting prompt"

variables:
  - name: name
    type: string
    description: "The name to greet"
    required: true

composition:
  - "Hello, {{ name }}!"
  - "How can I help you today?"
```

## Using the Prompt

```python
from pal import PromptCompiler
from pathlib import Path

# Initialize compiler
compiler = PromptCompiler()

# Compile the prompt
prompt = compiler.compile_from_file_sync(
    Path("hello.pal"),
    variables={"name": "Alice"}
)

print(prompt)
# Output:
# Hello, Alice!
# How can I help you today?
```

## Executing with an LLM

```python
import asyncio
from pal import PromptCompiler, PromptExecutor, OpenAIClient

async def main():
    # Setup
    compiler = PromptCompiler()
    client = OpenAIClient()  # Uses OPENAI_API_KEY env var
    executor = PromptExecutor(client)
    
    # Load and compile
    assembly = await compiler.loader.load_prompt_assembly_async("hello.pal")
    compiled = await compiler.compile(assembly, {"name": "Alice"})
    
    # Execute
    result = await executor.execute(
        compiled_prompt=compiled,
        prompt_assembly=assembly,
        model="gpt-4",
        temperature=0.7
    )
    
    print(result.response)

asyncio.run(main())
```

## Using Component Libraries

PAL supports reusable component libraries. Create `personas.pal.lib`:

```yaml
pal_version: "1.0"
library_id: "personas"
version: "1.0.0"
description: "Reusable AI personas"
type: persona

components:
  - name: helpful_assistant
    description: "A helpful AI assistant"
    content: |
      You are a helpful, harmless, and honest AI assistant.
      Always strive to provide accurate and useful information.
      
  - name: code_reviewer
    description: "An expert code reviewer"
    content: |
      You are an experienced software engineer conducting a code review.
      Focus on: correctness, performance, security, and maintainability.
```

Use the library in your prompt:

```yaml
pal_version: "1.0"
id: "code-review"
version: "1.0.0"
description: "Code review prompt"

imports:
  personas: "./personas.pal.lib"

variables:
  - name: code
    type: string
    description: "Code to review"
    required: true

composition:
  - "{{ personas.code_reviewer }}"
  - ""
  - "Please review this code:"
  - "```"
  - "{{ code }}"
  - "```"
```

## CLI Usage

PAL includes a CLI for quick testing:

```bash
# Compile a prompt
pal compile my_prompt.pal --var name=Alice

# Execute with a mock client
pal execute my_prompt.pal --mock

# Validate prompt syntax
pal validate my_prompt.pal
```

## Next Steps

- Read the [Writing Prompts Guide](guides/writing-prompts.md)
- Explore [Component Libraries](guides/component-libraries.md)
- See [API Reference](api/compiler.rst)