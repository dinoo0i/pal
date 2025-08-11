"""PAL CLI interface."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import click
import structlog
from rich.console import Console
from rich.json import JSON
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table

from ..core.compiler import PromptCompiler
from ..core.evaluation import EvaluationReporter, EvaluationRunner
from ..core.executor import (
    AnthropicClient,
    BaseLLMClient,
    MockLLMClient,
    OpenAIClient,
    PromptExecutor,
)
from ..core.loader import Loader
from ..exceptions.core import PALError

console = Console()
error_console = Console(stderr=True)
logger = structlog.get_logger()


def setup_logging(verbose: bool = False) -> None:
    """Set up structured logging."""
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer(),
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )


def handle_error(error: Exception) -> None:
    """Handle and display errors consistently."""
    if isinstance(error, PALError):
        error_console.print(f"[red]Error:[/red] {error}")
        if hasattr(error, "context") and error.context:
            error_console.print("[dim]Context:[/dim]")
            for key, value in error.context.items():
                error_console.print(f"  {key}: {value}")
    else:
        error_console.print(f"[red]Unexpected error:[/red] {error}")


def _load_variables(variables: str | None, vars_file: Path | None) -> dict[str, Any]:
    """Load variables from file and/or command line."""
    vars_dict: dict[str, Any] = {}

    if vars_file:
        with open(vars_file, encoding="utf-8") as f:
            vars_dict.update(json.load(f))

    if variables:
        try:
            vars_dict.update(json.loads(variables))
        except json.JSONDecodeError as e:
            error_console.print(f"[red]Invalid JSON in --vars:[/red] {e}")
            sys.exit(1)

    return vars_dict


def _create_llm_client(
    provider: str, api_key: str | None, mock_message: str | None = None
) -> BaseLLMClient:
    """Create LLM client based on provider."""
    if provider == "openai":
        return OpenAIClient(api_key)
    if provider == "anthropic":
        return AnthropicClient(api_key)
    # mock
    message = mock_message or "This is a mock response from the PAL system."
    return MockLLMClient(message)


async def _run_execution_async(
    pal_file: Path,
    vars_dict: dict[str, Any],
    llm_client: BaseLLMClient,
    model: str,
    temperature: float,
    max_tokens: int | None,
    log_file: Path | None,
    output: Path | None,
    json_output: bool,
) -> None:
    """Run the async execution logic."""
    compiler = PromptCompiler()
    loader = Loader()

    prompt_assembly = await loader.load_prompt_assembly_async(pal_file)
    compiled_prompt = await compiler.compile(prompt_assembly, vars_dict, pal_file)

    executor = PromptExecutor(llm_client, log_file)
    result = await executor.execute(
        compiled_prompt, prompt_assembly, model, temperature, max_tokens
    )

    _output_result(result, output, json_output, model)


def _output_result(
    result: Any, output: Path | None, json_output: bool, model: str
) -> None:
    """Output the execution result."""
    if output:
        if json_output:
            output.write_text(result.model_dump_json(indent=2), encoding="utf-8")
        else:
            output.write_text(result.response, encoding="utf-8")
        console.print(f"[green]✓[/green] Response written to {output}")
    else:
        if json_output:
            json_obj = JSON.from_data(result.model_dump())
            console.print(json_obj)
        else:
            panel = Panel(
                result.response,
                title=f"Response from {model}",
                subtitle=f"Tokens: {result.input_tokens}→{result.output_tokens} | Time: {result.execution_time_ms:.1f}ms",
            )
            console.print(panel)


def _get_files_to_validate(path: Path, recursive: bool) -> list[Path]:
    """Get list of files to validate."""
    files_to_check = []

    if path.is_file():
        files_to_check.append(path)
    elif path.is_dir():
        pattern = "**/*.pal" if recursive else "*.pal"
        files_to_check.extend(path.glob(pattern))

        pattern_lib = "**/*.pal.lib" if recursive else "*.pal.lib"
        files_to_check.extend(path.glob(pattern_lib))

    return files_to_check


def _validate_files(
    files_to_check: list[Path], loader: Any, compiler: Any, base_path: Path
) -> tuple[Table, int, int]:
    """Validate files and return results table."""
    table = Table(title="PAL Validation Results")
    table.add_column("File", style="cyan")
    table.add_column("Type", style="magenta")
    table.add_column("Status", style="green")
    table.add_column("Issues", style="red")

    total_files = len(files_to_check)
    valid_files = 0

    for file_path in files_to_check:
        file_type, status, issues, is_valid = _validate_single_file(
            file_path, loader, compiler
        )

        if is_valid:
            valid_files += 1

        table.add_row(
            str(file_path.relative_to(base_path.parent)), file_type, status, issues
        )

    return table, total_files, valid_files


def _validate_single_file(
    file_path: Path, loader: Any, compiler: Any
) -> tuple[str, str, str, bool]:
    """Validate a single file and return validation results."""
    try:
        if file_path.suffix == ".pal":
            prompt_assembly = loader.load_prompt_assembly(file_path)
            file_type = "Assembly"

            # Additional validation - check template variables
            template_vars = compiler.analyze_template_variables(prompt_assembly)
            defined_vars = {var.name for var in prompt_assembly.variables}
            undefined_vars = (
                template_vars - defined_vars - {"loop", "super"}
            )  # Jinja builtins

            if undefined_vars:
                issues = f"Undefined variables: {', '.join(sorted(undefined_vars))}"
                status = "[yellow]Warning[/yellow]"
                return file_type, status, issues, False
            return file_type, "[green]Valid[/green]", "", True

        if file_path.suffix == ".lib" and file_path.name.endswith(".pal.lib"):
            loader.load_component_library(file_path)
            return "Library", "[green]Valid[/green]", "", True

        return "Unknown", "[yellow]Skipped[/yellow]", "", False

    except Exception as e:
        issues = str(e)[:50] + "..." if len(str(e)) > 50 else str(e)
        return "Unknown", "[red]Invalid[/red]", issues, False


async def _run_evaluation_async(
    eval_file: Path,
    pal_file: Path | None,
    llm_client: BaseLLMClient,
    model: str,
    temperature: float,
    max_tokens: int | None,
    output: Path | None,
    output_format: str,
) -> None:
    """Run evaluation asynchronously."""
    loader = Loader()
    compiler = PromptCompiler(loader)
    executor = PromptExecutor(llm_client)
    runner = EvaluationRunner(loader, compiler, executor)

    result = await runner.run_evaluation(
        eval_file, pal_file, model, temperature=temperature, max_tokens=max_tokens
    )

    _generate_evaluation_report(result, output, output_format)
    _show_evaluation_summary(result, output, output_format)


def _generate_evaluation_report(
    result: Any, output: Path | None, output_format: str
) -> None:
    """Generate and output evaluation report."""
    reporter = EvaluationReporter()

    if output_format == "json":
        report_data = reporter.generate_json_report(result)
        if output:
            output.write_text(json.dumps(report_data, indent=2), encoding="utf-8")
            console.print(f"[green]✓[/green] Evaluation report written to {output}")
        else:
            console.print(JSON.from_data(report_data))
    else:  # console format
        report_text = reporter.generate_console_report(result)
        if output:
            output.write_text(report_text, encoding="utf-8")
            console.print(f"[green]✓[/green] Evaluation report written to {output}")
        else:
            console.print(report_text)


def _show_evaluation_summary(
    result: Any, output: Path | None, output_format: str
) -> None:
    """Show evaluation summary and exit if there were failures."""
    if result.pass_rate == 1.0:
        console.print(f"[green]✓ All {result.total_tests} tests passed![/green]")
    else:
        console.print(
            f"[yellow]⚠ {result.failed_tests}/{result.total_tests} tests failed[/yellow]"
        )
        if not output or output_format == "json":
            # Show brief failure summary
            for test_result in result.test_results:
                if not test_result.passed:
                    error_console.print(f"[red]✗[/red] {test_result.test_case.name}")
        sys.exit(1)


@click.group()
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose logging")
def cli(verbose: bool) -> None:
    """PAL - Prompt Assembly Language CLI."""
    setup_logging(verbose)


@cli.command("compile")
@click.argument("pal_file", type=click.Path(exists=True, path_type=Path))
@click.option("--vars", "-v", "variables", help="Variables as JSON string")
@click.option(
    "--vars-file",
    type=click.Path(exists=True, path_type=Path),
    help="Load variables from JSON file",
)
@click.option(
    "--output",
    "-o",
    type=click.Path(path_type=Path),
    help="Output file (default: stdout)",
)
@click.option("--no-format", is_flag=True, help="Disable syntax highlighting")
def compile_command(
    pal_file: Path,
    variables: str | None,
    vars_file: Path | None,
    output: Path | None,
    no_format: bool,
) -> None:
    """Compile a PAL file into a prompt string."""
    try:
        # Load variables
        vars_dict = _load_variables(variables, vars_file)

        # Compile the prompt
        compiler = PromptCompiler()
        compiled_prompt = compiler.compile_from_file_sync(pal_file, vars_dict)

        # Output
        if output:
            output.write_text(compiled_prompt, encoding="utf-8")
            console.print(f"[green]✓[/green] Compiled prompt written to {output}")
        else:
            if no_format:
                console.print(compiled_prompt)
            else:
                syntax = Syntax(
                    compiled_prompt, "markdown", theme="monokai", word_wrap=True
                )
                panel = Panel(syntax, title=f"Compiled Prompt: {pal_file.name}")
                console.print(panel)

    except Exception as e:
        handle_error(e)
        sys.exit(1)


@cli.command()
@click.argument("pal_file", type=click.Path(exists=True, path_type=Path))
@click.option("--model", "-m", required=True, help="LLM model to use")
@click.option(
    "--provider",
    type=click.Choice(["openai", "anthropic", "mock"]),
    default="mock",
    help="LLM provider",
)
@click.option("--vars", "-v", "variables", help="Variables as JSON string")
@click.option(
    "--vars-file",
    type=click.Path(exists=True, path_type=Path),
    help="Load variables from JSON file",
)
@click.option(
    "--temperature", "-t", type=float, default=0.7, help="Temperature for generation"
)
@click.option("--max-tokens", type=int, help="Maximum tokens to generate")
@click.option("--api-key", help="API key for the provider")
@click.option(
    "--log-file", type=click.Path(path_type=Path), help="Log execution details to file"
)
@click.option(
    "--output",
    "-o",
    type=click.Path(path_type=Path),
    help="Output file (default: stdout)",
)
@click.option("--json-output", is_flag=True, help="Output full result as JSON")
def execute(
    pal_file: Path,
    model: str,
    provider: str,
    variables: str | None,
    vars_file: Path | None,
    temperature: float,
    max_tokens: int | None,
    api_key: str | None,
    log_file: Path | None,
    output: Path | None,
    json_output: bool,
) -> None:
    """Compile and execute a PAL file with an LLM."""
    try:
        vars_dict = _load_variables(variables, vars_file)
        llm_client = _create_llm_client(provider, api_key)

        import asyncio

        asyncio.run(
            _run_execution_async(
                pal_file,
                vars_dict,
                llm_client,
                model,
                temperature,
                max_tokens,
                log_file,
                output,
                json_output,
            )
        )

    except Exception as e:
        handle_error(e)
        sys.exit(1)


@cli.command()
@click.argument("path", type=click.Path(exists=True, path_type=Path))
@click.option("--recursive", "-r", is_flag=True, help="Validate recursively")
def validate(path: Path, recursive: bool) -> None:
    """Validate PAL files for syntax and semantic errors."""
    try:
        loader = Loader()
        compiler = PromptCompiler(loader)

        files_to_check = _get_files_to_validate(path, recursive)
        if not files_to_check:
            console.print("[yellow]No PAL files found to validate[/yellow]")
            return

        table, total_files, valid_files = _validate_files(
            files_to_check, loader, compiler, path
        )

        console.print(table)
        console.print(
            f"\n[bold]Summary:[/bold] {valid_files}/{total_files} files valid"
        )

        if valid_files < total_files:
            sys.exit(1)

    except Exception as e:
        handle_error(e)
        sys.exit(1)


@cli.command()
@click.argument("pal_file", type=click.Path(exists=True, path_type=Path))
def info(pal_file: Path) -> None:
    """Show information about a PAL file."""
    try:
        loader = Loader()

        if pal_file.name.endswith(".pal.lib"):
            library = loader.load_component_library(pal_file)

            table = Table(title=f"Component Library: {library.library_id}")
            table.add_column("Property", style="cyan")
            table.add_column("Value", style="green")

            table.add_row("Library ID", library.library_id)
            table.add_row("Version", library.version)
            table.add_row("Type", library.type.value)
            table.add_row("Description", library.description)
            table.add_row("Components", str(len(library.components)))

            console.print(table)

            if library.components:
                comp_table = Table(title="Components")
                comp_table.add_column("Name", style="cyan")
                comp_table.add_column("Description", style="green")
                comp_table.add_column("Content Length", style="magenta")

                for comp in library.components:
                    comp_table.add_row(
                        comp.name,
                        comp.description[:50] + "..."
                        if len(comp.description) > 50
                        else comp.description,
                        str(len(comp.content)),
                    )

                console.print(comp_table)

        else:  # .pal file
            assembly = loader.load_prompt_assembly(pal_file)

            table = Table(title=f"Prompt Assembly: {assembly.id}")
            table.add_column("Property", style="cyan")
            table.add_column("Value", style="green")

            table.add_row("ID", assembly.id)
            table.add_row("Version", assembly.version)
            table.add_row("Description", assembly.description)
            if assembly.author:
                table.add_row("Author", assembly.author)
            table.add_row("Variables", str(len(assembly.variables)))
            table.add_row("Imports", str(len(assembly.imports)))
            table.add_row("Composition Items", str(len(assembly.composition)))

            console.print(table)

            if assembly.variables:
                var_table = Table(title="Variables")
                var_table.add_column("Name", style="cyan")
                var_table.add_column("Type", style="magenta")
                var_table.add_column("Required", style="green")
                var_table.add_column("Description", style="yellow")

                for var in assembly.variables:
                    var_table.add_row(
                        var.name,
                        var.type.value,
                        "✓" if var.required else "✗",
                        var.description,
                    )

                console.print(var_table)

            if assembly.imports:
                import_table = Table(title="Imports")
                import_table.add_column("Alias", style="cyan")
                import_table.add_column("Path/URL", style="green")

                for alias, path in assembly.imports.items():
                    import_table.add_row(alias, str(path))

                console.print(import_table)

    except Exception as e:
        handle_error(e)
        sys.exit(1)


@cli.command()
@click.argument("eval_file", type=click.Path(exists=True, path_type=Path))
@click.option(
    "--pal-file",
    type=click.Path(exists=True, path_type=Path),
    help="PAL file to evaluate (auto-detected if not provided)",
)
@click.option("--model", "-m", default="mock", help="LLM model to use for evaluation")
@click.option(
    "--provider",
    type=click.Choice(["openai", "anthropic", "mock"]),
    default="mock",
    help="LLM provider",
)
@click.option("--api-key", help="API key for the provider")
@click.option(
    "--temperature", "-t", type=float, default=0.7, help="Temperature for generation"
)
@click.option("--max-tokens", type=int, help="Maximum tokens to generate")
@click.option(
    "--output", "-o", type=click.Path(path_type=Path), help="Output report file"
)
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["console", "json"]),
    default="console",
    help="Output format",
)
def evaluate(
    eval_file: Path,
    pal_file: Path | None,
    model: str,
    provider: str,
    api_key: str | None,
    temperature: float,
    max_tokens: int | None,
    output: Path | None,
    output_format: str,
) -> None:
    """Run evaluation tests against a PAL file."""
    try:
        llm_client = _create_llm_client(
            provider, api_key, "This is a mock response for evaluation."
        )

        import asyncio

        asyncio.run(
            _run_evaluation_async(
                eval_file,
                pal_file,
                llm_client,
                model,
                temperature,
                max_tokens,
                output,
                output_format,
            )
        )

    except Exception as e:
        handle_error(e)
        sys.exit(1)


def main() -> None:
    """Main CLI entry point."""
    cli()
