"""
Test Runner Script for Crypto LLM Trading System.

Runs all tests with coverage reporting and categorization:
- Unit tests (components)
- Integration tests (E2E)
- Performance tests
- Full test suite

Usage:
    python scripts/run_tests.py                  # Run all tests
    python scripts/run_tests.py --unit           # Unit tests only
    python scripts/run_tests.py --integration    # Integration tests only
    python scripts/run_tests.py --performance    # Performance tests only
    python scripts/run_tests.py --coverage       # Run with coverage report
    python scripts/run_tests.py --verbose        # Verbose output
"""

import sys
import subprocess
import argparse
from pathlib import Path
from datetime import datetime


# ============================================================================
# Test Categories
# ============================================================================

UNIT_TESTS = [
    "tests/test_helpers.py",
    "tests/test_database.py",
    "tests/test_binance_client.py",
    "tests/test_llm_clients.py",
    "tests/test_core.py",
    "tests/test_services.py",
    "tests/test_api.py",
    "tests/test_scheduler.py"
]

INTEGRATION_TESTS = [
    "tests/test_integration_e2e.py",
    "tests/test_trading_cycles.py"
]

PERFORMANCE_TESTS = [
    "tests/test_performance.py"
]


# ============================================================================
# Color Output
# ============================================================================

class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'


def print_header(text):
    """Print colored header."""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.END}\n")


def print_success(text):
    """Print success message."""
    print(f"{Colors.GREEN}✅ {text}{Colors.END}")


def print_error(text):
    """Print error message."""
    print(f"{Colors.RED}❌ {text}{Colors.END}")


def print_warning(text):
    """Print warning message."""
    print(f"{Colors.YELLOW}⚠️  {text}{Colors.END}")


def print_info(text):
    """Print info message."""
    print(f"{Colors.CYAN}ℹ️  {text}{Colors.END}")


# ============================================================================
# Test Runner Functions
# ============================================================================

def run_pytest(test_files, verbose=False, coverage=False, markers=None):
    """
    Run pytest with specified parameters.

    Args:
        test_files: List of test files to run
        verbose: Show verbose output
        coverage: Generate coverage report
        markers: Pytest markers to filter tests

    Returns:
        Exit code from pytest
    """
    cmd = ["pytest"]

    # Add test files
    cmd.extend(test_files)

    # Add flags
    if verbose:
        cmd.append("-v")
    else:
        cmd.append("-q")

    if coverage:
        cmd.extend([
            "--cov=src",
            "--cov-report=term-missing",
            "--cov-report=html"
        ])

    if markers:
        cmd.extend(["-m", markers])

    # Show pytest command
    print_info(f"Running: {' '.join(cmd)}")
    print()

    # Run pytest
    result = subprocess.run(cmd)

    return result.returncode


def run_unit_tests(verbose=False, coverage=False):
    """Run all unit tests."""
    print_header("RUNNING UNIT TESTS")

    print_info(f"Test files: {len(UNIT_TESTS)}")
    for test_file in UNIT_TESTS:
        print(f"  - {test_file}")
    print()

    return run_pytest(UNIT_TESTS, verbose=verbose, coverage=coverage)


def run_integration_tests(verbose=False, coverage=False):
    """Run all integration tests."""
    print_header("RUNNING INTEGRATION TESTS")

    print_info(f"Test files: {len(INTEGRATION_TESTS)}")
    for test_file in INTEGRATION_TESTS:
        print(f"  - {test_file}")
    print()

    return run_pytest(INTEGRATION_TESTS, verbose=verbose, coverage=coverage)


def run_performance_tests(verbose=False):
    """Run performance tests."""
    print_header("RUNNING PERFORMANCE TESTS")

    print_info(f"Test files: {len(PERFORMANCE_TESTS)}")
    for test_file in PERFORMANCE_TESTS:
        print(f"  - {test_file}")
    print()

    # Performance tests don't need coverage
    return run_pytest(PERFORMANCE_TESTS, verbose=verbose, coverage=False)


def run_all_tests(verbose=False, coverage=False):
    """Run all tests."""
    print_header("RUNNING FULL TEST SUITE")

    all_tests = UNIT_TESTS + INTEGRATION_TESTS + PERFORMANCE_TESTS

    print_info(f"Total test files: {len(all_tests)}")
    print()

    return run_pytest(all_tests, verbose=verbose, coverage=coverage)


def check_pytest_installed():
    """Check if pytest is installed."""
    try:
        subprocess.run(
            ["pytest", "--version"],
            check=True,
            capture_output=True
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def install_test_dependencies():
    """Install test dependencies."""
    print_info("Installing test dependencies...")

    try:
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "pytest", "pytest-cov"],
            check=True
        )
        print_success("Test dependencies installed")
        return True
    except subprocess.CalledProcessError:
        print_error("Failed to install test dependencies")
        return False


def print_test_summary(exit_code, test_type, coverage_enabled):
    """Print test summary."""
    print()
    print("="*70)

    if exit_code == 0:
        print_success(f"{test_type} TESTS PASSED")
    else:
        print_error(f"{test_type} TESTS FAILED")

    if coverage_enabled:
        print_info("Coverage report saved to: htmlcov/index.html")

    print("="*70)
    print()


# ============================================================================
# Main Function
# ============================================================================

def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description="Crypto LLM Trading System - Test Runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/run_tests.py                      # Run all tests
  python scripts/run_tests.py --unit               # Unit tests only
  python scripts/run_tests.py --integration        # Integration tests only
  python scripts/run_tests.py --performance        # Performance tests only
  python scripts/run_tests.py --coverage           # With coverage report
  python scripts/run_tests.py --unit --coverage    # Unit tests with coverage
  python scripts/run_tests.py -v --coverage        # Verbose with coverage
        """
    )

    # Test category options
    parser.add_argument(
        "--unit",
        action="store_true",
        help="Run unit tests only"
    )
    parser.add_argument(
        "--integration",
        action="store_true",
        help="Run integration tests only"
    )
    parser.add_argument(
        "--performance",
        action="store_true",
        help="Run performance tests only"
    )

    # Output options
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Verbose output"
    )
    parser.add_argument(
        "--coverage",
        action="store_true",
        help="Generate coverage report"
    )

    args = parser.parse_args()

    # Print banner
    print()
    print(f"{Colors.BOLD}{Colors.CYAN}{'='*70}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}  🧪 CRYPTO LLM TRADING SYSTEM - TEST RUNNER{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'='*70}{Colors.END}")
    print()
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # Check pytest installed
    if not check_pytest_installed():
        print_warning("pytest not found")
        if not install_test_dependencies():
            sys.exit(1)

    # Determine which tests to run
    exit_code = 0

    if args.unit:
        exit_code = run_unit_tests(verbose=args.verbose, coverage=args.coverage)
        print_test_summary(exit_code, "UNIT", args.coverage)

    elif args.integration:
        exit_code = run_integration_tests(verbose=args.verbose, coverage=args.coverage)
        print_test_summary(exit_code, "INTEGRATION", args.coverage)

    elif args.performance:
        exit_code = run_performance_tests(verbose=args.verbose)
        print_test_summary(exit_code, "PERFORMANCE", False)

    else:
        # Run all tests
        exit_code = run_all_tests(verbose=args.verbose, coverage=args.coverage)
        print_test_summary(exit_code, "ALL", args.coverage)

    # Exit with pytest's exit code
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
