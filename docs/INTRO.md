## **Design Specification: Prompt Assembly Language (PAL)**

Based on the principles of modularity, versioning, dynamic assembly, and evaluation-driven development, this section presents a concrete architectural blueprint for a library to manage the prompt lifecycle. This proposed system is named the **Prompt Definition Framework (PAL)**. It is designed from the ground up to treat prompts as versioned, composable, and testable software artifacts, providing a robust foundation for building scalable and maintainable LLM applications.

### **1.1. Core Abstraction: The Prompt Schema (.prompt.yaml)**

The foundational element of PAL is the **Prompt Schema**, a declarative file that serves as the canonical source of truth for a given prompt. We propose using YAML for its excellent human readability and native support for comments, which is crucial for documentation. Each prompt in the system is defined by a .prompt.yaml file, which is intended to be stored in version control (e.g., Git) alongside the application code.

This schema-based approach enforces structure and provides a single, unambiguous definition for each prompt, capturing not just its content but also its metadata, interface, and composition logic.

**Example Schema: get_user_intent.prompt.yaml**

YAML

\

\# file: get_user_intent.prompt.yaml\
id: "get-user-intent-from-query"\
version: "1.3.0" # Semantic Versioning for the prompt \[41]\
description: "Classifies a user's query into one of the predefined intents for the web automation agent."\
author: "dev-team\@example.com"\
\
metadata:\
  tags: \[classification, routing, agent-core]\
  created_at: "2025-08-15"\
\
\# Defines the dynamic inputs required for runtime compilation\
variables:\
  - name: "user_query"\
    type: "string"\
    description: "The raw input from the user."\
  - name: "conversation_history"\
    type: "list"\
    description: "A list of previous user/assistant turns."\
  - name: "available_intents"\
    type: "list"\
    description: "A list of valid intent objects."\
\
\# A library of reusable prompt components\
components:\
  - name: "persona"\
    type: "Role"\
    content: "You are an expert routing system. Your sole purpose is to classify the user's intent based on the provided query and context. You are precise and concise."\
\
  - name: "intent_definitions"\
    type: "Context"\
    # Content is dynamically generated from the 'available_intents' variable\
    content: |\
      Available Intents:\
      {% for intent in available\_intents %}\
      - {{ intent.name }}: {{ intent.description }}\
      {% endfor %}\
\
  - name: "rules"\
    type: "Constraints"\
    content: |\
      - You MUST classify the intent into one of the \`Available Intents\`.\
      - If the intent is ambiguous, you MUST respond with the intent \`ambiguous_intent\`.\
      - Do not attempt to answer the user's query or engage in conversation.\
      - Your response must be only the specified JSON object.\
\
  - name: "examples"\
    type: "Examples" # Few-shot examples guide the model's behavior \[17, 19]\
    content:\
      - input: "take me to google.com"\
        output: '{"intent": "navigate_to_url", "parameters": {"url": "https\://google.com"}}'\
      - input: "what's the weather like?"\
        output: '{"intent": "search_for_term", "parameters": {"term": "weather"}}'\
      - input: "I can't tell what to do"\
        output: '{"intent": "ambiguous_intent", "parameters": {}}'\
\
  - name: "task"\
    type: "Task"\
    content: "Analyze the following user_query, considering the conversation_history and intent_definitions. Classify the user's intent and extract any relevant parameters."\
\
  - name: "output_format"\
    type: "OutputSchema"\
    content: "Respond ONLY with a single, valid JSON object containing two keys: 'intent' (string) and 'parameters' (an object of key-value pairs)."\
\
\# Defines the assembly order for the final prompt string, using delimiters\
composition:\
  - "### ROLE ###"\
  - "persona"\
  - "### AVAILABLE INTENTS ###"\
  - "intent_definitions"\
  - "### RULES ###"\
  - "rules"\
  - "### EXAMPLES ###"\
  - "examples"\
  - "### TASK ###"\
  - "task"\
  - "User Query: {{ user\_query }}"\
  - "Conversation History: {{ conversation\_history }}"\
  - "### OUTPUT FORMAT ###"\
  - "output_format"

**Table 3: The Prompt Definition Framework (PAL) Schema Specification**

|             |                         |          |                                                                                                                                                              |
| ----------- | ----------------------- | -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Field Name  | Data Type               | Required | Purpose                                                                                                                                                      |
| id          | String (kebab-case)     | Yes      | A unique, human-readable identifier for the prompt. Used to load the prompt programmatically.                                                                |
| version     | Semantic Version String | Yes      | The version of the prompt schema (e.g., "1.3.0"). Crucial for tracking changes and managing dependencies.                                                    |
| description | String                  | Yes      | A brief explanation of the prompt's purpose and intended use.                                                                                                |
| author      | String                  | No       | The person or team responsible for maintaining the prompt.                                                                                                   |
| metadata    | Object                  | No       | A key-value store for additional metadata, such as tags for categorization or creation/update timestamps.                                                    |
| variables   | Array of Objects        | No       | Defines the dynamic inputs required for runtime compilation. Each object specifies a variable's name, type, and description.                                 |
| components  | Array of Objects        | Yes      | The library of modular prompt parts. Each object has a name, type (e.g., Role, Context, Task), and content.                                                  |
| composition | Array of Strings        | Yes      | Defines the final assembly order of the prompt. It lists the names of components and can include literal strings (for delimiters) and variable placeholders. |

### **1.2. The Runtime Engine: Compiler & Executor**

PAL library requires a runtime engine to bring the declarative schemas to life. This engine consists of two main classes: a Compiler and an Executor.

- **Prompt Compiler:** This class is responsible for loading a .prompt.yaml schema and transforming it into a final, executable prompt string. Its primary method, compile(), accepts the id and version of the prompt to load, along with a dictionary of runtime variables. Its responsibilities include:

1. Loading and parsing the specified YAML schema file.

2. Validating that all required runtime variables have been provided.

3. Using a templating engine (like Jinja2) to inject the variables into the component content.

4. Assembling the final prompt string by iterating through the composition array, concatenating the rendered components and literal delimiters.

5. Handling more advanced logic, such as conditional inclusion of components based on an environment variable (e.g., 'dev' vs. 'prod').

- **Prompt Executor:** This class acts as a wrapper around the chosen LLM client (e.g., OpenAI, Anthropic). It is designed to provide a layer of observability and reliability for every LLM call. Its execute() method takes a compiled prompt string, a target model identifier (e.g., gpt-4o), and any necessary execution parameters (e.g., temperature, max_tokens). Its critical functions are:

1. **Pre-Execution Logging:** Before making the API call, it logs an immutable record containing the prompt schema id and version, the target model, the execution parameters, and the full compiled prompt string.

2. **API Call Execution:** It makes the actual call to the LLM provider's API.

3. **Post-Execution Logging:** After receiving the response, it logs the full raw response from the API, along with key performance metrics like latency, input/output token counts, and the estimated cost of the call. This creates a complete, auditable trace for every execution, which is invaluable for debugging, performance analysis, and cost management.<sup>27</sup>

### **1.3. The Evaluation Suite**

To enable Evaluation-Driven Development, PAL must include a structured way to define and run tests. This is accomplished with a parallel set of evaluation files and a test runner utility.

- **Evaluation Schema (.eval.yaml):** For each prompt schema, a corresponding .eval.yaml file can be created to define its test suite. This file links to a specific prompt version and contains a list of test cases.\
  **Example Schema: get_user_intent.eval.yaml**\
  YAML\
  \# file: get_user_intent.eval.yaml\
  prompt_id: "get-user-intent-from-query"\
  target_version: "1.3.0"\
  \
  test_cases:\
    - name: "simple_navigation_case"\
      variables:\
        user_query: "go to wikipedia"\
        available_intents: \[{name: 'navigate_to_url',...}]\
      assertions:\
        - type: "json_schema_match"\
          schema: {"intent": "string", "parameters": "object"}\
        - type: "json_field_equals"\
          path: "$.intent"\
          value: "navigate\_to\_url"\
  \
    - name: "ambiguous\_query\_case"\
      variables:\
        user\_query: "help me out here"\
        available\_intents: \[...]\
      assertions:\
        - type: "json\_field\_equals"\
          path: "$.intent"\
          value: "ambiguous_intent"

- **Test Runner:** This is a command-line tool or library function that discovers and executes these evaluation suites. For each test case, it compiles and executes the target prompt with the provided variables. It then runs the LLM's output through a series of assertion functions (e.g., checking for a valid JSON schema, comparing field values, or calculating semantic similarity). The runner aggregates the results and produces a report detailing the pass/fail rate for the prompt. This tool is designed to be integrated into a CI/CD pipeline, automatically running evaluations on every commit to prevent regressions from being deployed.<sup>32</sup>

### **1.4. Reference Implementation Blueprint (Python)**

To make this design concrete, a Python implementation would involve the following core classes:

- PromptSchema: A data class representing the parsed .prompt.yaml file.

- PromptCompiler: A class with a compile(schema, variables) method that returns a string.

- PromptExecutor: A class wrapping an LLM client with an execute(prompt_string, model) method that returns a response object containing the output and observability data.

- EvaluationRunner: A class that can load .eval.yaml files and run the defined test suites, returning a results summary.

This modular design separates the concerns of prompt definition, runtime assembly, execution, and evaluation, creating a clean, maintainable, and extensible library.

## **Section 2: Advanced Applications & Future-Proofing**

A well-designed framework should not only solve today's problems but also provide a robust foundation for the more complex AI systems of tomorrow. The Prompt Definition Framework (PAL) architecture is explicitly designed for this purpose. Its modular, versioned, and testable nature makes it the ideal building block for advanced applications like multi-agent systems and provides a strategic advantage in navigating the rapidly evolving LLM landscape.

### **2.1. Orchestrating Multi-Agent & Chained Prompts**

Complex tasks are rarely solved by a single LLM call. They often require a sequence of prompts (prompt chaining) or a collaboration between multiple specialized agents.<sup>47</sup> Building such systems on a foundation of brittle, unmanaged prompts is architecturally unsound. The reliability of a complex agentic system is a product of the reliability of its individual components. If each prompt call is inconsistent and untestable, the overall system will be exponentially more so. Therefore, a robust single-prompt management framework like PAL is a foundational prerequisite for building effective agents.

PAL architecture naturally extends to support these complex workflows. A "prompt chain" or "agent workflow" can be defined as a higher-order schema that orchestrates calls to multiple, versioned prompt schemas.

**Example Workflow Schema: search_and_summarize.workflow\.yaml**

YAML

\

id: "search-and-summarize-workflow"\
version: "1.0.0"\
description: "Takes a user query, performs a web search, and summarizes the results."\
\
variables:\
  - name: "initial_user_request"\
    type: "string"\
\
steps:\
  - name: "step1_extract_query"\
    prompt_id: "extract-search-term" # Reference to a PAL prompt schema\
    prompt_version: "1.1.0"\
    input_mapping:\
      user_query: "{{ initial\_user\_request }}"\
    output_variable: "search_term"\
\
  - name: "step2_perform_search"\
    type: "tool_call" # A step that calls an external tool, not an LLM\
    tool_name: "web_search_api"\
    input_mapping:\
      query: "{{ search\_term }}"\
    output_variable: "search_results"\
\
  - name: "step3_summarize_results"\
    prompt_id: "summarize-search-results"\
    prompt_version: "2.4.1"\
    input_mapping:\
      original_query: "{{ search\_term }}"\
      results_text: "{{ search\_results }}"\
    output_variable: "final_summary"

This approach allows complex reasoning chains, like those seen in Mixture-of-Agents (MoA) or Layered-CoT patterns, to be defined declaratively using tested, versioned, and reusable prompt components.<sup>49</sup>

### **2.2. Ensuring Cross-Model Compatibility & Mitigating Vendor Lock-in**

The LLM market is intensely competitive, with new, more powerful, or more cost-effective models being released frequently. An application that hardcodes its prompts and logic for a single model provider (e.g., OpenAI's API) incurs significant technical debt and vendor lock-in.<sup>39</sup> Migrating to a different provider, such as Anthropic or Google, would require a substantial and costly engineering effort to rewrite and re-test every prompt.

PAL provides a powerful abstraction layer to mitigate this risk and ensure strategic agility. The framework can be extended to manage model-specific variants within a single logical prompt definition. The application code continues to interact with a stable, logical prompt ID (e.g., get-user-intent), while the framework's Compiler and Executor handle the underlying complexity of choosing the correct prompt implementation for the target model.

**Example variants extension in .prompt.yaml:**

YAML

\

\# In get_user_intent.prompt.yaml\
...\
\# Default components for gpt-4o\
components:\
  - name: "persona"\
    type: "Role"\
    content: "You are an expert routing system..."\
...\
\# Model-specific overrides\
variants:\
  - model_family: "claude" # e.g., for claude-3.5-sonnet\
    composition: # Claude models respond well to XML tags and different ordering\
      - "\<prompt>"\
      - "persona"\
      - "\<examples>{{ examples }}\</examples>"\
      - "task"\
      - "\</prompt>"\
  - model_family: "gemini"\
    components: # Override the rules component specifically for Gemini\
      - name: "rules"\
        type: "Constraints"\
        content: "Follow these rules very carefully..."

With this extension, the PromptExecutor can be instructed to use a specific model. The PromptCompiler will then look for a matching variant and use its specialized components or composition, falling back to the default implementation if no variant is found. This turns a potentially massive code migration into a much simpler task of adding and validating new prompt configurations, de-risking the investment in AI and allowing the organization to leverage the best model for the job at any given time.
