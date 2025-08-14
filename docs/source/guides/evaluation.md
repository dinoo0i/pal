# PAL Evaluation Guide

The PAL evaluation system allows you to create automated test suites for your prompt assemblies, ensuring they produce consistent and correct outputs across different scenarios.

## Quick Start

### 1. Create an Evaluation File

Evaluation files use the `.eval.yaml` extension and define test cases for your prompts:

```yaml
pal_version: "1.0"
prompt_id: "my-prompt-id"
target_version: "1.0.0"
description: "Test suite for my prompt"

test_cases:
  - name: "basic_test"
    description: "Test basic functionality"
    variables:
      user_input: "Hello world"
    assertions:
      - type: "contains"
        config:
          text: "greeting"
          case_sensitive: false
```

### 2. Run Evaluations

```bash
# Run evaluation with mock LLM (for testing)
pal evaluate my_prompt.eval.yaml

# Run with a real model
pal evaluate my_prompt.eval.yaml --model gpt-4o --provider openai

# Specify a custom PAL file
pal evaluate tests.eval.yaml --pal-file custom.pal

# Output results to file
pal evaluate tests.eval.yaml --output results.json --output-format json
```

## Evaluation File Structure

### Required Fields

- `pal_version`: PAL specification version (currently "1.0")
- `prompt_id`: ID of the prompt assembly to test
- `target_version`: Expected version of the prompt assembly
- `test_cases`: List of test scenarios

### Test Case Structure

```yaml
test_cases:
  - name: "unique_test_name"
    description: "What this test validates"
    variables:
      # Variables to pass to the prompt
      param1: "value1"
      param2: ["list", "of", "values"]
    assertions:
      # List of assertions to validate the response
      - type: "assertion_type"
        config:
          # Assertion-specific configuration
```

## Available Assertions

### 1. Contains Assertion

Checks if the response contains specific text.

```yaml
- type: "contains"
  config:
    text: "expected text"
    case_sensitive: true  # Optional, defaults to true
```

### 2. Regex Match Assertion

Validates the response against a regular expression pattern.

```yaml
- type: "regex_match"
  config:
    pattern: "\\d{4}-\\d{2}-\\d{2}"  # Date pattern
    flags: 0  # Optional regex flags
```

### 3. JSON Valid Assertion

Ensures the response is valid JSON.

```yaml
- type: "json_valid"
  config: {}
```

### 4. JSON Field Equals Assertion

Checks if a specific JSON field equals an expected value.

```yaml
- type: "json_field_equals"
  config:
    path: "$.result.status"  # JSONPath-like syntax
    value: "success"
```

### 5. Length Assertion

Validates response length constraints.

```yaml
- type: "length"
  config:
    min_length: 100      # Minimum characters
    max_length: 1000     # Maximum characters
    # OR
    exact_length: 150    # Exact character count
```

## Advanced Features

### Variable Types

Test variables can be simple values or complex structures:

```yaml
variables:
  # Simple string
  user_query: "What is the weather?"
  
  # Number
  temperature: 72
  
  # List
  options: ["A", "B", "C"]
  
  # Object
  user_profile:
    name: "John Doe"
    age: 30
    preferences: ["tech", "sports"]
```

### Multiple Assertions per Test

Each test case can have multiple assertions:

```yaml
- name: "comprehensive_test"
  variables:
    input: "Generate a JSON response"
  assertions:
    - type: "json_valid"
      config: {}
    - type: "contains"
      config:
        text: "status"
    - type: "length"
      config:
        min_length: 50
        max_length: 500
```

### Auto-Discovery

If you don't specify a `--pal-file`, the evaluation runner will automatically search for a PAL file with the matching `prompt_id` in the same directory and subdirectories.

## Output Formats

### Console Output (Default)

```bash
pal evaluate tests.eval.yaml
```

Displays a human-readable report with pass/fail status and assertion details.

### JSON Output

```bash
pal evaluate tests.eval.yaml --output results.json --output-format json
```

Generates a detailed JSON report with:
- Summary statistics (total tests, pass rate)
- Individual test results
- Assertion details
- Execution metadata

## Best Practices

### 1. Test Edge Cases

Create test cases for various scenarios:

```yaml
test_cases:
  - name: "empty_input"
    variables:
      user_input: ""
    assertions:
      - type: "contains"
        config:
          text: "please provide input"

  - name: "long_input"
    variables:
      user_input: "{{ very_long_text }}"
    assertions:
      - type: "length"
        config:
          max_length: 2000
```

### 2. Use Descriptive Names

Make test names and descriptions clear:

```yaml
- name: "classification_high_confidence"
  description: "Verify classification returns high confidence for clear inputs"
```

### 3. Group Related Tests

Organize test cases logically:

```yaml
# Basic functionality tests
- name: "basic_greeting"
- name: "basic_farewell"

# Error handling tests  
- name: "empty_input_handling"
- name: "invalid_format_handling"

# Edge cases
- name: "very_long_input"
- name: "special_characters"
```

### 4. Version Compatibility

Always specify the target version to catch version mismatches:

```yaml
target_version: "2.1.0"  # Will warn if prompt version differs
```

## Integration with Development Workflow

### 1. Continuous Testing

Run evaluations as part of your development process:

```bash
# Test before committing changes
pal evaluate tests.eval.yaml

# Run with different models
pal evaluate tests.eval.yaml --model gpt-4o --provider openai
pal evaluate tests.eval.yaml --model claude-3-sonnet --provider anthropic
```

### 2. Regression Testing

Use evaluation files to catch regressions when modifying prompts:

1. Create comprehensive test suites covering expected behavior
2. Run tests before and after changes
3. Compare results to identify any degradation

### 3. Model Comparison

Evaluate the same prompt with different models:

```bash
pal evaluate tests.eval.yaml --model gpt-4o --output gpt4-results.json --output-format json
pal evaluate tests.eval.yaml --model claude-3-sonnet --output claude-results.json --output-format json
```

## Troubleshooting

### Common Issues

1. **Version Mismatch Warning**: The prompt version doesn't match `target_version`
   - Update the evaluation file or prompt version
   
2. **Prompt Not Found**: Auto-discovery can't find the PAL file
   - Use `--pal-file` to specify the exact path
   - Ensure the `prompt_id` matches the PAL file's `id`

3. **Assertion Failures**: Tests are failing unexpectedly
   - Check if the model output format has changed
   - Verify assertion configurations are correct
   - Use `--model mock` to test with predictable responses

### Debug Mode

Use verbose output to see detailed execution information:

```bash
pal evaluate tests.eval.yaml --verbose
```

This will show:
- Compiled prompt content
- Model responses
- Detailed assertion results
- Execution timing information

## Example: Complete Evaluation Suite

Here's a comprehensive example for a content classification prompt:

```yaml
pal_version: "1.0"
prompt_id: "content-classifier"
target_version: "1.2.0"
description: "Comprehensive test suite for content classification"

test_cases:
  - name: "clear_spam_classification"
    description: "Classify obvious spam content"
    variables:
      content: "URGENT!!! Win money now!!! Click here!!!"
      categories: ["spam", "legitimate", "promotional"]
    assertions:
      - type: "json_valid"
        config: {}
      - type: "json_field_equals"
        config:
          path: "$.category"
          value: "spam"
      - type: "json_field_equals"
        config:
          path: "$.confidence"
          value: "high"

  - name: "legitimate_content"
    description: "Classify normal business content"
    variables:
      content: "Thank you for your order. It will ship within 3-5 business days."
      categories: ["spam", "legitimate", "promotional"]
    assertions:
      - type: "json_valid"
        config: {}
      - type: "json_field_equals"
        config:
          path: "$.category"
          value: "legitimate"

  - name: "edge_case_empty"
    description: "Handle empty content gracefully"
    variables:
      content: ""
      categories: ["spam", "legitimate", "promotional"]
    assertions:
      - type: "json_valid"
        config: {}
      - type: "contains"
        config:
          text: "insufficient"
          case_sensitive: false

  - name: "response_format"
    description: "Ensure consistent response structure"
    variables:
      content: "Sample content for testing"
      categories: ["spam", "legitimate", "promotional"]
    assertions:
      - type: "json_valid"
        config: {}
      - type: "regex_match"
        config:
          pattern: '"category"\\s*:\\s*"(spam|legitimate|promotional)"'
      - type: "regex_match"
        config:
          pattern: '"confidence"\\s*:\\s*"(high|medium|low)"'
      - type: "length"
        config:
          min_length: 50
          max_length: 300
```

This evaluation suite tests multiple scenarios, validates JSON structure, checks specific field values, and ensures consistent response formatting.