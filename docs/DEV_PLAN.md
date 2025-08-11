## **Prompt Assembly Language (PAL) - Implementation Plan**

This document outlines the technical blueprint for building the PAL framework. The primary goal is to create a system that treats prompt engineering with the same rigor as software engineering, focusing on modularity, versioning, and testability.

### **1. Core Philosophy & Design Analogs**

Before diving into the implementation, it's crucial to establish the guiding philosophy by drawing parallels with successful DevOps tools:

- **PAL vs. Terraform:** Terraform uses HCL to declaratively define a desired infrastructure state. It has a `plan` step (compilation/diffing) and an `apply` step (execution). Similarly, PAL uses `.pal` files to declare a desired prompt structure. The **`pal compile`** command is our "plan" step, which renders the final prompt string. The execution is left to an LLM client, but the generation of the prompt is the core, testable output.
- **PAL vs. Docker Compose:** `docker-compose.yml` defines a multi-component application, linking services, volumes, and networks. This is analogous to how a `.pal` file imports and composes various `.pal.lib` component libraries. The `imports` section is our service discovery and linking mechanism.
- **Validation:** Both tools perform aggressive upfront validation. If `docker-compose.yml` has a typo or an invalid key, it fails immediately. If Terraform references a non-existent variable, it fails during the `plan`. PAL must adopt this "fail-fast" principle through rigorous schema validation and linting.

### **2. Phased Implementation Roadmap**

We will build PAL in three distinct, value-additive phases.

| Phase | Title                                       | Key Outcome                                                                                                              |
| :---- | :------------------------------------------ | :----------------------------------------------------------------------------------------------------------------------- |
| **1** | **The Core Engine: Compiler & Runtime**     | A functional CLI tool that can compile a `.pal` file with local imports into a final prompt string.                      |
| **2** | **Developer Experience: Linter & Tooling**  | A robust `linter` for static analysis and enhanced developer feedback loops within the IDE.                              |
| **3** | **The Ecosystem: Registry & Collaboration** | A public or private `registry` for sharing and discovering `.pal.lib` components, enabling true community collaboration. |

---

### **Phase 1: The Core Engine: Compiler & Runtime**

This phase focuses on creating the minimum viable product: a working compiler.

#### **2.1. Project Structure (for the library itself)**

```
/pal-compiler-py (or /pal-compiler-js)
|-- /pal
|   |-- __init__.py
|   |-- compiler.py       # Core compilation logic
|   |-- loader.py         # Handles file/URL loading and parsing
|   |-- resolver.py       # Handles import resolution and dependency graph
|   |-- models.py         # Pydantic/Zod schemas for validation
|   |-- exceptions.py     # Custom exceptions
|-- /cli
|   |-- main.py           # CLI command definitions (using Click/Commander)
|-- /tests
|-- setup.py (or package.json)
```

#### **2.2. The Compilation Process: A Step-by-Step Flow**

The `pal compile` command will trigger the following sequence:

1.  **Loading:** The `Loader` takes the path to the root `.pal` file. It reads the raw YAML content.
2.  **Parsing & Validation:** The raw content is parsed and immediately validated against a strict schema definition (Pydantic/Zod). If validation fails (e.g., missing `id`, `composition` is not a list), the process halts with a clear error. The output is a structured data object (e.g., a `PromptAssembly` class instance).
3.  **Dependency Resolution:** The `Resolver` inspects the `imports` dictionary of the `PromptAssembly` object.
    - It iterates through each alias and path (`traits: "./path/to/traits.pal.lib"`).
    - For each path, it recursively invokes the **Loader** to fetch, parse, and validate the `.pal.lib` file.
    - It detects and throws an error on circular dependencies.
    - It stores the validated `ComponentLibrary` objects in a dictionary, ready for the compiler. This is the "linking" step.
4.  **Templating & Rendering:** The `Compiler` receives the root `PromptAssembly` object, the resolved `ComponentLibrary` dependencies, and the runtime `variables` from the CLI.
    - It initializes a **Jinja2** (Python) or **Nunjucks** (Node.js) templating environment.
    - It iterates through the `composition` array.
    - For each item in the array, it renders the string using the templating engine. The context passed to the engine includes:
      - The `variables` dictionary (for `{{ ticket_body }}`).
      - The resolved dependencies, keyed by alias (for `{{ traits.sarcastic_helper }}`).
    - The rendered strings are concatenated to form the final, complete prompt.
5.  **Output:** The final string is printed to `stdout`.

#### **2.3. Schema Definition (using Python/Pydantic as an example)**

This is the key to robust validation.

`pal/models.py`

```python
from pydantic import BaseModel, FilePath, HttpUrl, Field
from typing import List, Dict, Literal, Union

class PalVariable(BaseModel):
    name: str
    type: str
    description: str

class PalComponent(BaseModel):
    name: str
    description: str
    content: str

class ComponentLibrary(BaseModel):
    pal_version: Literal["1.0"]
    library_id: str
    version: str = Field(pattern=r"^\d+\.\d+\.\d+$") # Enforce SemVer
    description: str
    type: Literal["persona", "task", "context", "rules", "examples", "output_schema", "reasoning", "trait", "note"]
    components: List[PalComponent]

class PromptAssembly(BaseModel):
    pal_version: Literal["1.0"]
    id: str
    version: str = Field(pattern=r"^\d+\.\d+\.\d+$")
    description: str
    author: str | None = None
    imports: Dict[str, Union[FilePath, HttpUrl]] = {}
    variables: List[PalVariable] = []
    composition: List[str]

```

#### **2.4. Technology Stack**

| Concern               | Python                      | Node.js        |
| :-------------------- | :-------------------------- | :------------- |
| **YAML Parsing**      | `PyYAML`                    | `js-yaml`      |
| **Schema Validation** | `Pydantic`                  | `Zod`          |
| **Templating**        | `Jinja2`                    | `Nunjucks`     |
| **CLI Framework**     | `Click` or `Typer`          | `Commander.js` |
| **HTTP Requests**     | `httpx` (for async support) | `axios`        |

---

### **Phase 2: Developer Experience: The Linter**

A compiler tells you if your code works; a linter tells you if your code is _good_. The `pal lint` command is crucial for adoption.

#### **2.5. Linter Functionality**

The linter will perform static analysis without executing the full compilation. It will:

1.  Parse and validate all `.pal` and `.pal.lib` files in a directory against the schemas defined in Phase 1.
2.  **Import Validation:** Check that all imported files exist at the specified paths.
3.  **Component Validation:** For every `{{ alias.component_name }}` in the `composition`, ensure that `alias` is defined in `imports` and that `component_name` exists in the corresponding library.
4.  **Variable Validation:**
    - Check for unused variables (defined in `variables` but not used in `composition`).
    - Check for undefined variables (used in `composition` but not defined in `variables`).
5.  **Style Checks (Future):** Enforce consistent naming conventions (e.g., kebab-case for `id`s, snake_case for `component_name`s).

The linter should be designed for IDE integration (e.g., as a VS Code extension) to provide real-time feedback.

---

### **Phase 3: The Ecosystem: Registry & Collaboration**

This phase transforms PAL from a tool into a platform.

#### **2.6. The PAL Registry**

This is a service analogous to `npm` or `PyPI`, but for prompts.

- **API:** A simple REST API will be needed:
  - `POST /publish`: To upload a new version of a `.pal.lib` package. Requires authentication.
  - `GET /resolve/{library_id}/{version}`: To get the URL or content of a specific library version.
- **CLI Integration:**
  - `pal login`: To authenticate with the registry.
  - `pal publish <path_to_lib>`: Bundles and uploads the library.
  - The `Resolver` from Phase 1 will be updated to handle registry identifiers (e.g., `imports: { common: "com.example/common-traits@1.2.1" }`). It will call the registry API to resolve this to a downloadable URL and then use the `Loader`.
- **Storage:** A cloud storage bucket (S3, GCS) is a perfect backend to store the published library files.

#### **2.7. The Visual PAL Builder**

While the spec is code-first, a visual builder will democratize the process.

- **Frontend:** A React/Vue/Svelte web application.
- **Backend:** A service that uses the PAL compiler library.
- **Functionality:**
  1.  Users can browse the PAL Registry to find and import component libraries.
  2.  They can visually assemble a prompt by dragging components into a `composition` list.
  3.  A form interface allows them to fill out metadata (`id`, `description`) and define `variables`.
  4.  **The key feature:** The visual builder **generates clean, well-formatted `.pal` files** that can be checked directly into version control. It's a UI for producing best-practice artifacts, not a black-box system.

### **4. Final CLI Interface**

The final CLI would look like this:

```sh
# Phase 1: Compile a prompt, passing variables as a JSON string
pal compile ./prompts/classify.pal \
  --vars '{"ticket_body": "my laptop is broken", "classification_categories": ["Hardware", "Software"]}'

# Phase 2: Lint an entire project directory for errors
pal lint .

# Phase 3: Interact with the registry
pal login
pal publish ./pal_libraries/custom/behavioral_traits.pal.lib
```

By following this phased, principles-driven approach, we can build the Prompt Assembly Language framework as a robust, scalable, and highly collaborative platform that elevates the discipline of prompt engineering.
