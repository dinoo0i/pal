# PAL - Prompt Assembly Language

[![Python](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![CI](https://github.com/cyqlelabs/pal/workflows/CI/badge.svg)](https://github.com/cyqlelabs/pal/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/cyqlelabs/pal/graph/badge.svg?token=Q3S48FGMQM)](https://codecov.io/gh/cyqlelabs/pal)

PAL (Prompt Assembly Language) is a framework for managing LLM prompts as versioned, composable software artifacts. It treats prompt engineering with the same rigor as software engineering, focusing on modularity, versioning, and testability.

See also the [NodeJS version](https://github.com/cyqlelabs/pal-node) of PAL (_WIP_)

## ⚡ Features

- **Modular Components**: Break prompts into reusable, versioned components
- **Template System**: Powerful Jinja2-based templating with variable injection
- **Dependency Management**: Import and compose components from local files or URLs
- **LLM Integration**: Built-in support for OpenAI, Anthropic, and custom providers
- **Evaluation Framework**: Comprehensive testing system for prompt validation
- **Rich CLI**: Beautiful command-line interface with syntax highlighting
- **Flexible Extensions**: Use `.pal/.pal.lib` or `.yml/.lib.yml` extensions
- **Type Safety**: Full Pydantic v2 validation for all schemas
- **Observability**: Structured logging and execution tracking

## 📦 Installation

```bash
# Install with uv (recommended)
uv add pal-framework

# Or with pip
pip install pal-framework
```

## 📁 Project Structure

```
my_pal_project/
├── prompts/
│   ├── classify_intent.pal     # or .yml for better IDE support
│   └── code_review.pal
├── libraries/
│   ├── behavioral_traits.pal.lib    # or .lib.yml
│   ├── reasoning_strategies.pal.lib
│   └── output_formats.pal.lib
└── evaluation/
    └── classify_intent.eval.yaml
```

## 🚀 Quick Start

### 1. Create a Component Library

For a detailed guide, [read this](docs/source/guides/component-libraries.md).

```yaml
# libraries/traits.pal.lib
pal_version: "1.0"
library_id: "com.example.traits"
version: "1.0.0"
description: "Behavioral traits for AI agents"
type: "trait"

components:
  - name: "helpful_assistant"
    description: "A helpful and polite assistant"
    content: |
      You are a helpful, harmless, and honest AI assistant. You provide
      accurate information while being respectful and considerate.
```

### 2. Create a Prompt Assembly


For a detailed guide, [read this](docs/source/guides/writing-prompts.md).

```yaml
# prompts/classify_intent.pal
pal_version: "1.0"
id: "classify-user-intent"
version: "1.0.0"
description: "Classifies user queries into intent categories"

imports:
  traits: "./libraries/traits.pal.lib"

variables:
  - name: "user_query"
    type: "string"
    description: "The user's input query"
  - name: "available_intents"
    type: "list"
    description: "List of available intent categories"

composition:
  - "{{ traits.helpful_assistant }}"
  - ""
  - "## Task"
  - "Classify this user query into one of the available intents:"
  - ""
  - "**Available Intents:**"
  - "{% for intent in available_intents %}"
  - "- {{ intent.name }}: {{ intent.description }}"
  - "{% endfor %}"
  - ""
  - "**User Query:** {{ user_query }}"
```

### 3. Use the CLI

```bash
# Compile a prompt
pal compile prompts/classify_intent.pal --vars '{"user_query": "Take me to google.com", "available_intents": [{"name": "navigate", "description": "Go to URL"}]}'

# Execute with an LLM
pal execute prompts/classify_intent.pal --model gpt-4 --provider openai --vars '{"user_query": "Take me to google.com", "available_intents": [{"name": "navigate", "description": "Go to URL"}]}'

# Validate PAL files
pal validate prompts/ --recursive

# Run evaluation tests
pal evaluate evaluation/classify_intent.eval.yaml
```

### 4. Use Programmatically

```python
import asyncio
from pal import PromptCompiler, PromptExecutor, MockLLMClient

async def main():
    # Set up components
    compiler = PromptCompiler()
    llm_client = MockLLMClient("Mock response")
    executor = PromptExecutor(llm_client)

    # Compile prompt
    variables = {
        "user_query": "What's the weather?",
        "available_intents": [{"name": "search", "description": "Search for info"}]
    }

    compiled_prompt = await compiler.compile_from_file(
        "prompts/classify_intent.pal",
        variables
    )

    print("Compiled Prompt:", compiled_prompt)

asyncio.run(main())
```

## 🧪 Evaluation System

Create test suites to validate your prompts:

```yaml
# evaluation/classify_intent.eval.yaml
pal_version: "1.0"
prompt_id: "classify-user-intent"
target_version: "1.0.0"

test_cases:
  - name: "navigation_test"
    variables:
      user_query: "Go to google.com"
      available_intents: [{ "name": "navigate", "description": "Visit URL" }]
    assertions:
      - type: "json_valid"
      - type: "contains"
        config:
          text: "navigate"
```

## 🏗️ Architecture

PAL follows modern software engineering principles:

- **Schema Validation**: All files are validated against strict Pydantic schemas
- **Dependency Resolution**: Automatic import resolution with circular dependency detection
- **Template Engine**: Jinja2 for powerful variable interpolation and logic
- **Observability**: Structured logging with execution metrics and cost tracking
- **Type Safety**: Full type hints and runtime validation

## 🛠️ CLI Commands

| Command        | Description                                       |
| -------------- | ------------------------------------------------- |
| `pal compile`  | Compile a PAL file into a prompt string           |
| `pal execute`  | Compile and execute a prompt with an LLM          |
| `pal validate` | Validate PAL files for syntax and semantic errors |
| `pal evaluate` | Run evaluation tests against prompts              |
| `pal info`     | Show detailed information about PAL files         |

## 🧩 Component Types

PAL supports different types of reusable components:

- **persona**: AI personality and role definitions
- **task**: Specific instructions or objectives
- **context**: Background information and knowledge
- **rules**: Constraints and guidelines
- **examples**: Few-shot learning examples
- **output_schema**: Output format specifications
- **reasoning**: Thinking strategies and methodologies
- **trait**: Behavioral characteristics
- **note**: Documentation and comments

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- 📚 [Documentation](#)
- 🐛 [Issues](https://github.com/cyqlelabs/pal/issues)
- 💬 [Discussions](https://github.com/cyqlelabs/pal/discussions)

## 🗺️ Roadmap

- [ ] **PAL Registry**: Centralized repository for sharing components
- [ ] **Visual Builder**: Drag-and-drop prompt composition interface
- [ ] **IDE Extensions**: VS Code and other editor integrations
