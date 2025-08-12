# Component Libraries

Component libraries allow you to create reusable prompt components that can be shared across multiple prompts.

## Creating a Library

Component libraries use the `.pal.lib` extension:

```yaml
pal_version: "1.0"
library_id: "my-components"
version: "1.0.0"
description: "Reusable components for my prompts"
type: persona  # Component type

components:
  - name: component_name
    description: "What this component does"
    content: |
      The actual content of the component
      Can be multiple lines
    metadata:
      tags: ["optional", "metadata"]
```

## Component Types

PAL defines standard component types:

- `persona` - AI personalities and roles
- `task` - Specific tasks or instructions
- `context` - Background information
- `rules` - Guidelines and constraints
- `examples` - Example inputs/outputs
- `output_schema` - Output format specifications
- `reasoning` - Reasoning strategies
- `trait` - Behavioral traits
- `note` - Additional notes

## Example Libraries

### Personas Library

```yaml
pal_version: "1.0"
library_id: "personas"
version: "2.0.0"
description: "AI personas for different use cases"
type: persona

components:
  - name: software_architect
    description: "Experienced software architect"
    content: |
      You are a senior software architect with 15+ years of experience.
      You specialize in system design, scalability, and best practices.
      You consider trade-offs and provide practical solutions.
      
  - name: code_reviewer
    description: "Thorough code reviewer"
    content: |
      You are an experienced code reviewer focused on:
      - Code quality and maintainability
      - Security vulnerabilities
      - Performance optimizations
      - Best practices and design patterns
      
  - name: friendly_tutor
    description: "Patient programming tutor"
    content: |
      You are a friendly and patient programming tutor.
      You explain concepts clearly with examples.
      You encourage questions and learning from mistakes.
```

### Output Formats Library

```yaml
pal_version: "1.0"
library_id: "output-formats"
version: "1.0.0"
description: "Standard output format specifications"
type: output_schema

components:
  - name: json_response
    description: "JSON formatted response"
    content: |
      Provide your response in valid JSON format:
      {
        "summary": "Brief summary",
        "details": ["point 1", "point 2"],
        "recommendations": []
      }
      
  - name: markdown_report
    description: "Markdown formatted report"
    content: |
      Format your response as a Markdown report:
      # Title
      ## Summary
      ## Analysis
      ## Recommendations
      ## Conclusion
      
  - name: yaml_config
    description: "YAML configuration format"
    content: |
      Return a YAML configuration:
      ```yaml
      setting_name: value
      features:
        - feature1
        - feature2
      ```
```

### Reasoning Strategies Library

```yaml
pal_version: "1.0"
library_id: "reasoning"
version: "1.0.0"
description: "Problem-solving strategies"
type: reasoning

components:
  - name: chain_of_thought
    description: "Step-by-step reasoning"
    content: |
      Let's approach this step-by-step:
      1. First, identify the key components
      2. Then, analyze relationships
      3. Finally, synthesize a solution
      
  - name: pros_and_cons
    description: "Balanced analysis"
    content: |
      Analyze by listing:
      Pros:
      - Advantage 1
      - Advantage 2
      
      Cons:
      - Disadvantage 1
      - Disadvantage 2
      
      Recommendation based on balance
      
  - name: first_principles
    description: "Break down to fundamentals"
    content: |
      Breaking this down to first principles:
      - What are the fundamental truths?
      - What assumptions can we challenge?
      - How can we build up from basics?
```

## Using Libraries in Prompts

### Basic Import and Usage

```yaml
pal_version: "1.0"
id: "code-analysis"
version: "1.0.0"

imports:
  personas: "./personas.pal.lib"
  formats: "./output-formats.pal.lib"

composition:
  - "{{ personas.code_reviewer }}"
  - ""
  - "Review this code:"
  - "{{ code }}"
  - ""
  - "{{ formats.json_response }}"
```

### Multiple Library Imports

```yaml
imports:
  p: "./personas.pal.lib"
  f: "./formats.pal.lib"
  r: "./reasoning.pal.lib"
  e: "./examples.pal.lib"

composition:
  - "{{ p.software_architect }}"
  - "{{ r.first_principles }}"
  - "{{ e.api_examples }}"
  - "{{ f.yaml_config }}"
```

### Remote Library Import

```yaml
imports:
  shared: "https://github.com/org/pal-libs/raw/main/shared.pal.lib"
  local: "./local-overrides.pal.lib"

composition:
  - "{{ shared.standard_header }}"
  - "{{ local.custom_instructions }}"
```

## Library Organization

### Recommended Structure

```
project/
├── prompts/
│   ├── api-design.pal
│   ├── code-review.pal
│   └── documentation.pal
├── libraries/
│   ├── personas.pal.lib
│   ├── tasks.pal.lib
│   ├── formats.pal.lib
│   └── domain/
│       ├── finance.pal.lib
│       └── healthcare.pal.lib
```

### Version Management

Use semantic versioning for libraries:

```yaml
# Version 1.0.0 - Initial release
version: "1.0.0"

# Version 1.1.0 - Added new components
version: "1.1.0"

# Version 2.0.0 - Breaking changes
version: "2.0.0"
```

## Best Practices

### 1. Single Responsibility

Each library should focus on one type of component:

```yaml
# Good - focused library
library_id: "error-handling"
type: rules
components:
  - name: validation_rules
  - name: error_messages
  - name: recovery_strategies

# Bad - mixed concerns
library_id: "misc"
components:
  - name: persona1
  - name: output_format
  - name: random_task
```

### 2. Descriptive Names

Use clear, descriptive names for components:

```yaml
# Good
- name: detailed_code_reviewer
  description: "Reviews code for quality, security, and performance"

# Bad
- name: reviewer
  description: "Reviews stuff"
```

### 3. Documentation

Include comprehensive descriptions:

```yaml
components:
  - name: security_auditor
    description: "Security-focused code auditor"
    content: |
      You are a security auditor specialized in:
      - OWASP Top 10 vulnerabilities
      - Authentication and authorization
      - Data validation and sanitization
    metadata:
      expertise: ["security", "compliance"]
      certifications: ["CISSP", "CEH"]
```

### 4. Modularity

Design components to work independently:

```yaml
# Good - self-contained
- name: api_designer
  content: |
    You design RESTful APIs following best practices:
    - Clear resource naming
    - Proper HTTP methods
    - Consistent error handling

# Bad - depends on external context
- name: designer
  content: |
    You design things based on the previous instructions
```

## Testing Libraries

Test your libraries with a simple test prompt:

```python
from pal import PromptCompiler, Loader

async def test_library():
    loader = Loader()
    
    # Load and validate library
    library = await loader.load_component_library_async("personas.pal.lib")
    print(f"Loaded {len(library.components)} components")
    
    # Test in a prompt
    test_prompt = """
    pal_version: "1.0"
    id: "test"
    version: "1.0.0"
    imports:
      p: "./personas.pal.lib"
    composition:
      - "{{ p.software_architect }}"
    """
    
    # Save and compile
    with open("test.pal", "w") as f:
        f.write(test_prompt)
    
    compiler = PromptCompiler()
    result = await compiler.compile_from_file(Path("test.pal"))
    print(result)
```

## Sharing Libraries

Libraries can be shared via:

1. **Git repositories** - Version control and collaboration
2. **Package registries** - npm, PyPI, etc.
3. **Direct URLs** - GitHub raw links, CDNs
4. **Internal networks** - Corporate repositories

Example packaging for distribution:

```json
// package.json for npm
{
  "name": "@org/pal-libraries",
  "version": "1.0.0",
  "files": ["*.pal.lib"],
  "repository": "github:org/pal-libraries"
}
```