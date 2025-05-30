# Bitflux MCP Development Guide

## Build/Run Commands
- Run server: `python main.py` or `uv run main.py`
- Run with SSE transport: `python main.py --sse --port 8888`
- Install/update dependencies: `uv sync`
- Run specific package tests: `cd pkg/<package_name> && python -m pytest`
- Lint/format: No specific commands configured (use standard Python tools)

## Project Structure
- Main entry: `main.py` → `server.main()`
- MCP server implementation: `server/cli.py`
- Tool implementations: `server/tools/`
- Workspace packages: `pkg/` (downloadstats, ec2_tools, machine_lookup, bitflux_catcher_api)

## Code Style Guidelines
- Use type hints for all function parameters and return values
- Import organization: standard library, third-party, local imports (blank lines between)
- Class naming: PascalCase with descriptive suffixes (e.g., `GetEC2PricingTool`)
- Function/variable naming: snake_case
- Async functions: Use `async def` for MCP tool implementations
- Error handling: Try/catch with structured error responses including status/message
- Tool descriptions: Detailed docstrings with parameters, examples, and usage notes
- Constants: Use class attributes for tool `name` and `description`
- Context logging: Use `await ctx.error()` for error logging in tools

## Dependencies
- Uses `uv` for package management and workspace handling
- FastMCP framework for MCP server implementation
- boto3 for AWS integration
- Custom workspace packages for specific functionality
