#!/usr/bin/env python
"""
Run tests for Fast Agents with proper configuration for async tests.
"""
import sys
import pytest
import argparse
from pathlib import Path

def main():
    """Run the Fast Agents test suite."""
    parser = argparse.ArgumentParser(description='Run Fast Agents tests')
    parser.add_argument('--unit', action='store_true', help='Run only unit tests')
    parser.add_argument('--integration', action='store_true', help='Run only integration tests')
    parser.add_argument('--all', action='store_true', help='Run all tests (default)')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    parser.add_argument('--coverage', action='store_true', help='Generate coverage report')
    parser.add_argument('--html', action='store_true', help='Generate HTML report')
    parser.add_argument('--pattern', type=str, default=None, help='Test pattern to match')
    parser.add_argument('--fix', action='store_true', help='Run only tests that failed last time')
    parser.add_argument('--debug', action='store_true', help='Run in debug mode')
    parser.add_argument('--module', type=str, default=None, help='Run tests for specific module')
    parser.add_argument('--file', type=str, default=None, help='Run tests from specific file')
    parser.add_argument('--function', type=str, default=None, help='Run specific test function')

    args = parser.parse_args()
    # Determine which tests to run
    if not (args.unit or args.integration or args.all or args.module or args.file or args.function):
        args.all = True  # Default to all tests
    # Set up the test directory
    test_dir = Path(__file__).parent / 'tests'
    # Build pytest arguments
    pytest_args = ['-xvs']  # Always use verbose mode and show output
    # Add debug mode if requested
    if args.debug:
        pytest_args.append('--no-header')
        pytest_args.append('--showlocals')

    # Add coverage if requested
    if args.coverage:
        pytest_args.extend(['--cov=fast_agents', '--cov-report=term'])
        if args.html:
            pytest_args.append('--cov-report=html')
    # Add HTML report if requested
    if args.html and not args.coverage:
        pytest_args.append('--html=test-report.html')
    # Add test pattern if specified
    if args.pattern:
        pytest_args.append(f'-k {args.pattern}')
    # Add last failed option if fix flag is set
    if args.fix:
        pytest_args.append('--lf')

    # Determine which test paths to run
    test_paths = []
    if args.function:
        # Run a specific test function
        if args.file:
            test_paths.append(f"{args.file}::{args.function}")
        elif args.module:
            test_paths.append(f"tests/*/{args.module}.py::{args.function}")
        else:
            test_paths.append(f"tests/*/*/*{args.function}")
    elif args.file:
        # Run tests from a specific file
        test_paths.append(args.file)
    elif args.module:
        # Run tests for a specific module
        test_paths.append(f"tests/*/{args.module}.py")
    else:
        # Default path selection based on unit/integration flags
        if args.all or args.unit:
            test_paths.append(str(test_dir / 'unit'))
        if args.all or args.integration:
            test_paths.append(str(test_dir / 'integration'))
    # Add test paths to pytest arguments
    pytest_args.extend(test_paths)
    print(f"Running tests with arguments: {' '.join(pytest_args)}")
    # Run the tests
    result = pytest.main(pytest_args)
    # Exit with pytest's return code
    sys.exit(result)

if __name__ == '__main__':
    main()