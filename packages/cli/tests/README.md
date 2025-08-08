# CLI Testing Documentation

## Overview

This document describes the comprehensive testing strategy for the Shelly Manager CLI package. The tests follow dependency injection patterns without patching, ensuring clean and maintainable test code.

## Test Structure

```
tests/
├── conftest.py                     # Shared fixtures and configuration
├── unit/                          # Unit tests
│   ├── test_main.py              # Main CLI module tests
│   ├── commands/                 # Command group tests
│   │   ├── test_device_commands.py
│   │   ├── test_device_commands.py
│   │   ├── test_config_commands.py
│   │   ├── test_bulk_commands.py
│   │   ├── test_export_commands.py
│   │   └── test_common.py        # Common utilities tests
│   └── dependencies/             # Dependency injection tests
│       └── test_container.py     # CLI container tests
└── integration/                  # Integration tests
    └── test_cli_flows.py        # Full CLI workflow tests
```

## Testing Principles

### 1. Dependency Injection Over Patching
- All dependencies are injected through the CLI container
- No use of `@patch` or `mock.patch` decorators
- Clean separation between test setup and execution

### 2. Fixtures for Reusability
- Comprehensive fixture library in `conftest.py`
- Fixtures for all major domain objects
- Mock containers and interactors for isolation

### 3. Async Testing Support
- Full support for async commands
- Proper async/await patterns in tests
- AsyncMock for async interactor methods

### 4. Click Testing Integration
- Uses Click's `CliRunner` for command testing
- Proper CLI context injection
- Command line argument validation

## Key Fixtures

### Core Fixtures
- `runner`: Click test runner
- `mock_container`: Mocked CLI container with all dependencies
- `cli_context`: Prepared CLI context with mocks
- `sample_device`: Sample Shelly device for testing
- `sample_devices`: List of sample devices
- `sample_action_result`: Sample action result object

### Interactor Mocks
- `mock_scan_interactor`: For device scanning operations
- `mock_status_interactor`: For device status checks
- `mock_reboot_interactor`: For device reboot operations
- `mock_update_interactor`: For firmware updates
- `mock_config_get_interactor`: For configuration retrieval
- `mock_config_set_interactor`: For configuration updates

## Test Categories

### Unit Tests

#### Main Module (`test_main.py`)
- CLI initialization and help display
- Version information display
- Command line argument parsing
- Context setup with configuration files

#### Device Commands (`test_device_commands.py`)
- Device scanning (IP ranges, config-based)
- Device listing and status checking
- Device rebooting with confirmation
- Device configuration management
- Device firmware and configuration updates (moved to device commands)
- Error handling for invalid inputs

#### Config Commands (`test_config_commands.py`)
- Configuration retrieval and display
- Configuration updates with JSON data
- IP address management (add/remove/clear)
- Configuration validation
- Confirmation prompts and force flags

#### Bulk Commands (`test_bulk_commands.py`)
- Bulk reboot operations
- Bulk update operations
- Bulk status checking
- Target specification (scan/config/IPs)
- Confirmation and force operations

#### Export Commands (`test_export_commands.py`)
- Device data export (JSON/CSV)
- Configuration inclusion in exports
- Export format validation
- Output file handling
- Error handling for export failures

#### Common Utilities (`test_common.py`)
- IP address parsing and validation
- IP range parsing (CIDR, dash notation)
- Async command decorator testing
- Click option decorators
- Scan request creation

#### Container Tests (`test_container.py`)
- Dependency injection container setup
- Singleton instance management
- Configuration file path resolution
- Service lifecycle management
- Cross-interactor dependency sharing

### Integration Tests

#### CLI Flows (`test_cli_flows.py`)
- End-to-end command workflows
- Multi-command scenarios
- Error handling across commands
- Context persistence between commands
- Configuration file integration

## Running Tests

### Local Development
```bash
# From CLI package directory
cd packages/cli

# Run all tests
python -m pytest tests/ -v

# Run specific test category
python -m pytest tests/unit/commands/ -v
python -m pytest tests/integration/ -v

# Run with coverage
python -m pytest tests/ --cov=cli --cov-report=html

# Run specific test file
python -m pytest tests/unit/commands/test_device_commands.py -v
```

### Using Test Runner
```bash
# From CLI package directory
python run_tests.py
```

### From Project Root
```bash
# Run CLI tests specifically
make test-cli

# Run all tests
make test
```

## Test Patterns

### Basic Command Test
```python
async def test_command_with_valid_input(
    self, runner, mock_interactor, expected_result, cli_context
):
    mock_interactor.execute = AsyncMock(return_value=expected_result)

    result = runner.invoke(
        command_group,
        ["command", "argument"],
        obj=cli_context,
        catch_exceptions=False,
    )

    assert result.exit_code == 0
    mock_interactor.execute.assert_called_once()
```

### Error Handling Test
```python
def test_command_with_invalid_input(self, runner, cli_context):
    result = runner.invoke(
        command_group,
        ["command", "invalid-input"],
        obj=cli_context,
        catch_exceptions=False,
    )

    assert result.exit_code != 0
    assert "error message" in result.output
```

### Confirmation Test
```python
def test_command_requires_confirmation(self, runner, cli_context):
    result = runner.invoke(
        command_group,
        ["dangerous-command"],
        obj=cli_context,
        input="n\n",  # User says no
        catch_exceptions=False,
    )

    assert result.exit_code == 1
```

## Best Practices

1. **No Comments in Tests**: Test names should be self-descriptive
2. **Dependency Injection**: Always use injected dependencies, never patch
3. **Async Awareness**: Use AsyncMock for async methods
4. **Error Testing**: Test both success and failure scenarios
5. **User Interaction**: Test confirmation prompts and user input
6. **File Operations**: Use pytest's tmp_path for file testing
7. **Isolation**: Each test should be independent and repeatable

## Coverage Goals

- **Unit Tests**: 90%+ coverage of all command logic
- **Integration Tests**: Cover major user workflows
- **Error Paths**: Test all error conditions and edge cases
- **User Interactions**: Test all confirmation prompts and input validation

## Future Enhancements

1. **Performance Tests**: Add tests for command execution time
2. **Memory Tests**: Monitor memory usage during bulk operations
3. **Stress Tests**: Test with large device lists
4. **Output Format Tests**: Validate exact output formatting
5. **Configuration Tests**: Test various configuration file formats
