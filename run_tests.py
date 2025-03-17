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

    if not (args.unit or args.integration or args.all or args.module or args.file or args.function):
        args.all = True
    test_dir = Path(__file__).parent / 'tests'
    pytest_args = ['-xvs']

    if args.debug:
        pytest_args.extend(['--no-header', '--showlocals'])

    if args.coverage:
        pytest_args.extend(['--cov=fast_agents', '--cov-report=term'])
        if args.html:
            pytest_args.append('--cov-report=html')
    elif args.html:
        pytest_args.append('--html=test-report.html')
    if args.pattern:
        pytest_args.append(f'-k {args.pattern}')
    if args.fix:
        pytest_args.append('--lf')
    test_paths = []
    if args.function:
        test_paths.append(f"{args.file or f'tests/*/{args.module}.py' if args.module else 'tests/*/*/*'}::{args.function}")
    elif args.file:
        test_paths.append(args.file)
    elif args.module:
        test_paths.append(f"tests/*/{args.module}.py")
    else:
        if args.all or args.unit:
            test_paths.append(str(test_dir / 'unit'))
        if args.all or args.integration:
            test_paths.append(str(test_dir / 'integration'))

    pytest_args.extend(test_paths)
    print(f"Running tests with arguments: {' '.join(pytest_args)}")
    sys.exit(pytest.main(pytest_args))

if __name__ == '__main__':
    main()