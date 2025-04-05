# AgentNexus Testing Guide

This directory contains tests for the AgentNexus framework. The tests are organized into unit tests and integration tests.

## Test Categories

### Unit Tests

Unit tests focus on testing individual components of the AgentNexus framework:

- **Manifest Generation**: Tests for generating agent manifests and configuring agents
- **Agent Actions**: Tests for registering and executing agent actions
- **Workflows**: Tests for workflow registration, step execution, and transitions
- **UI Components**: Tests for UI component creation and event handling
- **Session Management**: Tests for session creation, retrieval, and updates

### Integration Tests

Integration tests focus on testing how components work together:

- **Complete Agent Workflow**: Tests for end-to-end agent functionality with actions and workflows

## Running Tests

You can run the tests using the `run_tests.py` script:

```bash
# Run all tests
python run_tests.py --all

# Run only unit tests
python run_tests.py --unit

# Run only integration tests
python run_tests.py --integration

# Run tests with coverage report
python run_tests.py --coverage

# Run tests with HTML report
python run_tests.py --html

# Run tests matching a pattern
python run_tests.py --pattern "manifest"
```

You can also run tests directly with pytest:

```bash
# Run all tests
pytest tests/

# Run unit tests
pytest tests/unit/

# Run a specific test file
pytest tests/unit/test_manifest_generation.py
```

## Test Dependencies

The tests depend on the following packages:

- pytest: Testing framework
- pytest-cov: Coverage reporting
- pytest-html: HTML report generation
- fastapi: For API testing
- httpx: For HTTP client (used by TestClient)

You can install these dependencies with:

```bash
pip install pytest pytest-cov pytest-html fastapi httpx
```

## Mocking External Dependencies

The tests use mocks to avoid actual connections to external services:

- **Redis**: All Redis connections are mocked to prevent actual Redis connections
- **FastAPI**: Tests use FastAPI's TestClient for API testing without an actual server
- **Session Manager**: Tests mock the session manager to avoid actual session creation/retrieval

## Adding New Tests

When adding new tests, follow these guidelines:

1. **Unit Tests**: Place tests for individual components in the appropriate file in the `unit/` directory
2. **Integration Tests**: Place tests for combined functionality in the `integration/` directory
3. **Fixtures**: Add common fixtures to `conftest.py`
4. **Mocking**: Use mocks for external dependencies
5. **Test Coverage**: Aim for high test coverage of critical code paths

## Test Coverage Report

You can generate a test coverage report with:

```bash
python run_tests.py --coverage --html
```

This will generate a HTML coverage report in the `htmlcov/` directory.

## Continuous Integration

TBD