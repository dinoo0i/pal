## Specification: The Prompt Assembly Language (PAL) v1.0

### 1. Introduction & Philosophy

The Prompt Assembly Language (PAL) is a declarative specification for defining, composing, and managing Large Language Model (LLM) prompts as versioned software artifacts. It is designed to facilitate modularity, reusability, and collaboration in the development of complex AI systems.

The core philosophy of PAL is to treat prompts not as monolithic strings, but as dynamic compositions of discrete, version-controlled components. [3,4] This approach enables developers and prompt engineers to build, test, and share standardized parts—such as behavioral traits, reasoning strategies, rule sets, and output formats—across different projects and teams. [5,6]

PAL is designed to be:

- **Human-Readable:** Using a clear YAML structure for ease of authoring and review.
- **Modular:** Breaking down prompts into the smallest logical, reusable parts. [7,8]
- **Composable:** Allowing complex prompts to be assembled from a library of components.
- **Shareable:** Enabling the import of component libraries from local files or remote repositories.
- **Versioned:** Integrating seamlessly with existing version control systems like Git to track changes to both prompts and their constituent components. [9,10]

### 2. File Structure

A PAL project is organized into two primary file types:

- **Prompt Assembly Files (`.pal`):** The main file that defines a specific, executable prompt by importing and composing components.
- **Component Library Files (`.pal.lib`):** Files that define a collection of reusable components of a specific type (e.g., traits, rules, formats).

A recommended project structure:

```markdown
/my_agent_project
|-- /prompts
| |-- classify_intent.pal
| |-- summarize_text.pal
|-- /pal_libraries
| |-- /custom
| | |-- behavioral_traits.pal.lib
| | |-- output_formats.pal.lib
| | |-- reasoning_strategies.pal.lib
|-- pal_project.yaml (Project-level configuration)
```

### 3. Component Library Specification (`.pal.lib`)

A Component Library is a file dedicated to a specific category of reusable prompt parts. This structure promotes high cohesion and loose coupling, foundational principles of extensible software design. [1]

**Schema:**

```yaml
# The version of the PAL protocol this library adheres to.
pal_version: "1.0"

# A unique, namespaced identifier for this library.
library_id: "com.example.common.traits.behavioral"
version: "1.2.1" # Semantic version for this library file.
description: "A collection of common behavioral traits for AI agents."

# Defines the type of components contained within.
# Allowed values: "persona", "task", "context", "rules", "examples", "output_schema", "reasoning", "trait", "note"
type: "trait"

# The collection of reusable components.
components:
  - name: "meticulous"
    description: "A trait for careful, detail-oriented reasoning."
    content: |
      You are meticulous and detail-oriented. You think through every step of your reasoning process to ensure accuracy before providing a final answer.

  - name: "sarcastic_helper"
    description: "A trait for a witty but ultimately helpful assistant."
    content: |
      You have a sarcastic and witty personality. While your tone may be dry, your ultimate goal is to be exceptionally helpful and accurate.

  - name: "concise"
    description: "A trait for providing brief, to-the-point answers."
    content: "Your responses are always direct and to the point. You avoid any conversational filler or unnecessary pleasantries."
```

### 4. Prompt Assembly Specification (`.pal`)

The Prompt Assembly file is the core executable definition. It imports necessary libraries and defines the final composition of the prompt string.

**Schema:**

```yaml
# The version of the PAL protocol this file adheres to.
pal_version: "1.0"

# --- METADATA ---
id: "classify-support-ticket"
version: "2.1.0" # Semantic version for this specific prompt assembly.
description: "Classifies an incoming support ticket using a configurable personality."
author: "agent-dev-team@example.com"

# --- IMPORTS ---
# Imports component libraries from local files or remote URLs.
# This is the key to sharing and reusing components across projects.
imports:
  # Alias: path/url
  traits: "./pal_libraries/custom/behavioral_traits.pal.lib"
  formats: "./pal_libraries/custom/output_formats.pal.lib"
  reasoning: "./pal_libraries/custom/reasoning_strategies.pal.lib"

# --- INTERFACE ---
# Defines the dynamic variables required at runtime.
variables:
  - name: "ticket_body"
    type: "string"
    description: "The raw text content of the support ticket."
  - name: "classification_categories"
    type: "list"
    description: "A list of valid categories for classification."

# --- COMPOSITION ---
# Defines the final assembly order of the prompt.
# References components using the 'alias.component_name' syntax.
composition:
  - "### ROLE AND BEHAVIOR ###"
  - "You are an expert support ticket classification agent."
  - "{{ traits.sarcastic_helper }}" # <-- Imported behavioral trait

  - "### TASK ###"
  - "Analyze the support ticket provided in the context and classify it into one of the available categories."

  - "### REASONING STRATEGY ###"
  - "{{ reasoning.chain_of_thought }}" # <-- Imported reasoning strategy

  - "### AVAILABLE CATEGORIES ###"
  - |
    {% for category in classification_categories %}
    - {{ category }}
    {% endfor %}

  - "### CONTEXT: TICKET CONTENT ###"
  - "<ticket_content>"
  - "{{ ticket_body }}"
  - "</ticket_content>"

  - "### OUTPUT FORMAT ###"
  - "You MUST adhere to the following output format."
  - "{{ formats.strict_json_object }}" # <-- Imported output format
```

### 5. Example Component Libraries (`.pal.lib`)

These examples illustrate how different "thinking processes" and formats can be modularized.

#### `reasoning_strategies.pal.lib`

```yaml
pal_version: "1.0"
library_id: "com.example.common.strategies.reasoning"
version: "1.0.0"
description: "A collection of standard reasoning strategies."
type: "reasoning"
components:
  - name: "chain_of_thought"
    description: "Instructs the model to think step-by-step."
    content: "Think through the problem step-by-step to ensure you arrive at the correct conclusion. Lay out your reasoning before giving the final answer."
  - name: "rephrase_and_respond"
    description: "Instructs the model to rephrase the query before answering."
    content: "First, rephrase and expand upon the user's query to ensure you have understood it correctly. Then, provide your answer."
```

#### `output_formats.pal.lib`

```yaml
pal_version: "1.0"
library_id: "com.example.common.formats.output"
version: "1.4.0"
description: "A collection of standardized output format instructions."
type: "output_schema"
components:
  - name: "strict_json_object"
    description: "Ensures the output is ONLY a valid JSON object."
    content: "Your response MUST be a single, valid JSON object and nothing else. Do not include any explanatory text, markdown formatting, or conversational pleasantries before or after the JSON object."
  - name: "markdown_table"
    description: "Ensures the output is a markdown table with specific columns."
    content: "Format your response as a Markdown table with the following columns: | Item | Analysis | Recommendation |."
```

### 6. The PAL Ecosystem

The PAL protocol is designed to be the foundation of a broader ecosystem of tools that bring software engineering rigor to AI development: [9,11]

- **PAL Compiler:** A runtime engine that parses `.pal` and `.pal.lib` files, resolves all imports, injects runtime `variables`, and assembles the final, executable prompt string.
- **PAL Linter:** A static analysis tool that validates PAL files against the specification, checking for syntax errors, broken imports, and unused variables.
- **PAL Registry:** A centralized, version-aware repository (akin to npm or PyPI) where teams and the community can publish and share `pal.lib` packages. This would dramatically accelerate development by providing access to pre-vetted, high-quality components for common tasks (e.g., `pip install pal-common-rules-pii-redaction`).
- **Visual PAL Builder:** A graphical user interface where developers or even non-technical users can build agents by dragging, dropping, and connecting components from imported libraries. The UI would generate the clean, version-controlled `.pal` files in the background, bridging the gap between low-code development and engineering best practices. [5,6]

By adopting this protocol, we create a system where the "mind" of an agent is no longer a fragile, monolithic artifact but a well-structured, maintainable, and endlessly extensible assembly of shared, community-vetted ideas.

