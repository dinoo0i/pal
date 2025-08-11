# Contributing to PAL

Thank you for your interest in contributing to PAL (Prompt Assembly Language)! We welcome contributions from the community and are grateful for your help in making PAL better.

## 🚀 Getting Started

### Prerequisites

- Python 3.12 or higher
- [uv](https://github.com/astral-sh/uv) package manager (recommended)
- Git

### Setting up the Development Environment

1. **Fork and clone the repository:**
   ```bash
   git clone https://github.com/your-username/pal.git
   cd pal
   ```

2. **Install dependencies:**
   ```bash
   # Using uv (recommended)
   uv sync

   # Or using pip
   pip install -e ".[dev]"
   ```

3. **Run tests to ensure everything is working:**
   ```bash
   uv run pytest
   ```

## 📝 How to Contribute

### Types of Contributions

We welcome various types of contributions:

- 🐛 **Bug fixes**
- ✨ **New features**
- 📚 **Documentation improvements**
- 🧪 **Test coverage improvements**
- 🎨 **Code quality improvements**
- 🔧 **Tool and infrastructure improvements**

### Before You Start

1. **Check existing issues** - Look for existing issues or discussions related to your contribution
2. **Open an issue** - For significant changes, please open an issue first to discuss your approach
3. **Follow conventions** - Review the codebase to understand existing patterns and conventions

## 🛠️ Development Workflow

### Making Changes

1. **Create a feature branch:**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes** following the guidelines below

3. **Write or update tests** for your changes

4. **Run the test suite:**
   ```bash
   uv run pytest
   ```

5. **Run linting and formatting:**
   ```bash
   uv run ruff check .
   uv run ruff format .
   ```

6. **Update documentation** if needed

### Commit Guidelines

We follow conventional commit messages:

- `feat: add new component type for personas`
- `fix: resolve template compilation error`
- `docs: update installation instructions`
- `test: add evaluation system tests`
- `refactor: simplify dependency resolution logic`

### Pull Request Process

1. **Push your branch** to your fork
2. **Open a Pull Request** with:
   - Clear title and description
   - Reference to related issues
   - Summary of changes made
   - Any breaking changes noted
3. **Ensure CI passes** - All tests and checks must pass
4. **Request review** from maintainers
5. **Address feedback** promptly

## 📋 Code Standards

### Python Code Style

- Follow [PEP 8](https://pep8.org/) guidelines
- Use type hints for all functions and methods
- Write docstrings for all public functions, classes, and modules
- Use Pydantic models for data validation
- Keep functions focused and small

### PAL File Standards

- Follow the PAL schema specifications
- Include comprehensive metadata (version, description, etc.)
- Use semantic versioning for components
- Provide clear examples in component documentation

### Testing

- Write unit tests for all new functionality
- Include integration tests for complex features
- Add evaluation tests for prompt-related changes
- Aim for high test coverage
- Use descriptive test names

### Documentation

- Update README.md if adding new features
- Add docstrings to all public APIs
- Include examples in docstrings where helpful
- Update CLI help text for new commands

## 🧪 Running Tests

### Full Test Suite
```bash
uv run pytest
```

### Specific Test Categories
```bash
# Unit tests only
uv run pytest tests/unit/

# Integration tests
uv run pytest tests/integration/

# Evaluation tests
uv run pytest tests/evaluation/
```

### Coverage Report
```bash
uv run pytest --cov=pal --cov-report=html
```

## 🏗️ Project Structure

Understanding the project structure will help you navigate and contribute effectively:

```
pal/
├── src/pal/                 # Main package source
│   ├── compiler/           # Prompt compilation logic
│   ├── executor/           # LLM execution logic
│   ├── evaluation/         # Testing and validation
│   ├── cli/               # Command-line interface
│   └── schemas/           # Pydantic models
├── tests/                 # Test suite
│   ├── unit/             # Unit tests
│   ├── integration/      # Integration tests
│   └── fixtures/         # Test data
├── docs/                 # Documentation
└── examples/             # Example PAL files
```

## 🔍 Component Types

When contributing new component types or improving existing ones:

- **persona**: AI personality and role definitions
- **task**: Specific instructions or objectives  
- **context**: Background information and knowledge
- **rules**: Constraints and guidelines
- **examples**: Few-shot learning examples
- **output_schema**: Output format specifications
- **reasoning**: Thinking strategies and methodologies
- **trait**: Behavioral characteristics
- **note**: Documentation and comments

## 🐛 Reporting Issues

### Bug Reports

Please include:
- PAL version
- Python version
- Operating system
- Minimal reproducible example
- Expected vs actual behavior
- Error messages and stack traces

### Feature Requests

Please include:
- Clear description of the feature
- Use cases and motivation
- Proposed implementation approach (if applicable)
- Any breaking changes considerations

## 📞 Getting Help

- 📚 [Documentation](https://pal-framework.readthedocs.io/)
- 🐛 [Issues](https://github.com/pal-framework/pal/issues)
- 💬 [Discussions](https://github.com/pal-framework/pal/discussions)

## 📄 License

By contributing to PAL, you agree that your contributions will be licensed under the same MIT License that covers the project.

---

Thank you for contributing to PAL! 🎉