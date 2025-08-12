# Writing PAL Prompts

This guide covers the fundamentals of writing effective PAL prompts.

## Basic Structure

Every PAL prompt file (`.pal`) follows this structure:

```yaml
pal_version: "1.0"
id: "unique-identifier"
version: "1.0.0"  # Semantic versioning
description: "What this prompt does"

imports:  # Optional
  alias: "./path/to/library.pal.lib"

variables:  # Optional
  - name: variable_name
    type: string
    description: "Variable description"
    required: true
    default: "optional default value"

metadata:  # Optional
  author: "Your Name"
  tags: ["category", "use-case"]

composition:
  - "Line 1 of your prompt"
  - "Line 2 with {{ variable_name }}"
  - "{{ alias.component_name }}"
```

## Variables

### Variable Types

PAL supports these variable types:

- `string` - Text values
- `integer` - Whole numbers
- `float` - Decimal numbers  
- `boolean` - true/false
- `list` - Arrays of values
- `dict` - Key-value pairs
- `any` - Any type (use sparingly)

### Variable Definition

```yaml
variables:
  - name: api_name
    type: string
    description: "Name of the API to design"
    required: true
    
  - name: max_endpoints
    type: integer
    description: "Maximum number of endpoints"
    required: false
    default: 10
    
  - name: features
    type: list
    description: "List of features to include"
    required: true
    
  - name: config
    type: dict
    description: "Configuration options"
    required: false
```

## Templating with Jinja2

PAL uses Jinja2 for templating. All standard Jinja2 features are supported:

### Basic Variable Substitution

```yaml
composition:
  - "Design an API for {{ api_name }}"
  - "The API should support {{ features | length }} features"
```

### Conditionals

```yaml
composition:
  - "{% if advanced_mode %}"
  - "Include advanced features like caching and rate limiting"
  - "{% else %}"
  - "Focus on basic CRUD operations"
  - "{% endif %}"
```

### Loops

```yaml
composition:
  - "Required features:"
  - "{% for feature in features %}"
  - "- {{ feature }}"
  - "{% endfor %}"
```

### Filters

```yaml
composition:
  - "API Name: {{ api_name | upper }}"
  - "Endpoints: {{ endpoints | join(', ') }}"
  - "Description: {{ description | title }}"
```

## Using Component Libraries

### Importing Libraries

```yaml
imports:
  personas: "./libraries/personas.pal.lib"
  tasks: "./libraries/tasks.pal.lib"
  formats: "https://example.com/formats.pal.lib"
```

### Using Components

```yaml
composition:
  - "{{ personas.expert_developer }}"
  - ""
  - "{{ tasks.code_review }}"
  - ""
  - "Code to review:"
  - "{{ code }}"
  - ""
  - "{{ formats.json_output }}"
```

## Best Practices

### 1. Use Descriptive IDs

```yaml
# Good
id: "api-design-restful-v2"

# Bad  
id: "prompt1"
```

### 2. Version Your Prompts

Use semantic versioning to track changes:

```yaml
version: "1.2.3"
# Major.Minor.Patch
# Major: Breaking changes
# Minor: New features
# Patch: Bug fixes
```

### 3. Provide Clear Descriptions

```yaml
description: "Generates RESTful API specifications from requirements"

variables:
  - name: requirements
    type: string
    description: "Business requirements in plain English"  # Clear!
```

### 4. Organize with Composition

Break complex prompts into logical sections:

```yaml
composition:
  # System message
  - "{{ personas.api_designer }}"
  - ""
  
  # Context
  - "## Context"
  - "{{ context }}"
  - ""
  
  # Task
  - "## Task"
  - "Design a RESTful API based on these requirements:"
  - "{{ requirements }}"
  - ""
  
  # Output format
  - "## Output Format"
  - "{{ formats.openapi_spec }}"
```

### 5. Use Metadata

```yaml
metadata:
  author: "Jane Doe"
  created: "2024-01-01"
  tags: ["api", "design", "openapi"]
  tested_with: ["gpt-4", "claude-3"]
```

## Advanced Patterns

### Multi-line Content

For complex content, use YAML's multi-line syntax:

```yaml
composition:
  - |
    This is a multi-line string
    that preserves line breaks
    and formatting.
  - >
    This is a folded string that
    will be rendered as a single
    line with spaces.
```

### Dynamic Component Selection

```yaml
variables:
  - name: expertise_level
    type: string
    description: "beginner, intermediate, or expert"

composition:
  - "{% if expertise_level == 'beginner' %}"
  - "{{ personas.patient_teacher }}"
  - "{% elif expertise_level == 'expert' %}"
  - "{{ personas.technical_expert }}"
  - "{% else %}"
  - "{{ personas.helpful_assistant }}"
  - "{% endif %}"
```

### Nested Templates

```yaml
composition:
  - "{% for section in sections %}"
  - "## {{ section.title }}"
  - "{{ section.content }}"
  - "{% if section.examples %}"
  - "Examples:"
  - "{% for example in section.examples %}"
  - "- {{ example }}"
  - "{% endfor %}"
  - "{% endif %}"
  - "{% endfor %}"
```

## Testing Your Prompts

Always test your prompts with various inputs:

```python
from pal import PromptCompiler

compiler = PromptCompiler()

# Test with different variable values
test_cases = [
    {"api_name": "UserService", "features": ["auth", "profile"]},
    {"api_name": "PaymentAPI", "features": ["stripe", "paypal", "crypto"]},
]

for variables in test_cases:
    prompt = compiler.compile_from_file_sync("api_design.pal", variables)
    print(f"Test case: {variables['api_name']}")
    print(prompt)
    print("-" * 40)
```