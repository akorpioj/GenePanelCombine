#!/usr/bin/env python3
"""
Database Testing Runner

This script provides convenient commands for running database-specific tests
and generating reports focused on database operations and data integrity.
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def run_database_tests(test_type='all', coverage=True, html_report=True, verbose=False):
    """
    Run database tests with specified options.
    
    Args:
        test_type (str): Type of database tests to run
        coverage (bool): Whether to generate coverage report
        html_report (bool): Whether to generate HTML report
        verbose (bool): Whether to run in verbose mode
    """
    cmd = ['python', '-m', 'pytest']
    
    # Test selection based on type
    if test_type == 'unit':
        cmd.extend(['-m', 'unit and database'])
    elif test_type == 'integration':
        cmd.extend(['-m', 'integration and database'])
    elif test_type == 'migrations':
        cmd.extend(['tests/unit/test_database_migrations.py'])
    elif test_type == 'performance':
        cmd.extend(['-m', 'database and slow'])
    elif test_type == 'schema':
        cmd.extend(['-k', 'schema or migration'])
    elif test_type == 'integrity':
        cmd.extend(['-k', 'integrity or constraint'])
    else:  # 'all'
        cmd.extend(['-m', 'database'])
    
    # Coverage options
    if coverage:
        cmd.extend([
            '--cov=app.models',
            '--cov=app.extensions',
            '--cov-report=term-missing'
        ])
        
        if html_report:
            cmd.extend(['--cov-report=html:htmlcov/database'])
    
    # Verbose output
    if verbose:
        cmd.append('-v')
    
    # Additional pytest options
    cmd.extend([
        '--tb=short',
        '--disable-warnings'
    ])
    
    print(f"Running command: {' '.join(cmd)}")
    return subprocess.run(cmd)


def run_database_benchmarks():
    """Run database performance benchmarks."""
    cmd = [
        'python', '-m', 'pytest',
        '-m', 'database and slow',
        '-v',
        '--tb=short',
        '--benchmark-only' if 'pytest-benchmark' in sys.modules else '--durations=10'
    ]
    
    print("Running database performance benchmarks...")
    return subprocess.run(cmd)


def run_database_schema_validation():
    """Run database schema validation tests."""
    cmd = [
        'python', '-m', 'pytest',
        'tests/unit/test_database_migrations.py::TestDatabaseSchemaValidation',
        '-v',
        '--tb=short'
    ]
    
    print("Running database schema validation...")
    return subprocess.run(cmd)


def run_database_stress_tests():
    """Run database stress tests."""
    cmd = [
        'python', '-m', 'pytest',
        '-m', 'database and slow',
        '-k', 'stress or large or concurrent',
        '-v',
        '--tb=line'
    ]
    
    print("Running database stress tests...")
    return subprocess.run(cmd)


def generate_database_test_report():
    """Generate comprehensive database test report."""
    print("Generating comprehensive database test report...")
    
    # Run all database tests with detailed reporting
    cmd = [
        'python', '-m', 'pytest',
        '-m', 'database',
        '--cov=app.models',
        '--cov=app.extensions', 
        '--cov-report=html:htmlcov/database',
        '--cov-report=xml:coverage_database.xml',
        '--junitxml=database_test_results.xml',
        '-v',
        '--tb=short'
    ]
    
    result = subprocess.run(cmd)
    
    if result.returncode == 0:
        print("\n✅ Database test report generated successfully!")
        print("📊 HTML Coverage Report: htmlcov/database/index.html")
        print("📋 JUnit XML Report: database_test_results.xml")
        print("📈 Coverage XML Report: coverage_database.xml")
    else:
        print("\n❌ Database test report generation failed!")
    
    return result


def main():
    """Main CLI interface for database testing."""
    parser = argparse.ArgumentParser(
        description='Database Testing Runner for GenePanelCombine',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_database_tests.py                    # Run all database tests
  python run_database_tests.py --type unit        # Run unit database tests only
  python run_database_tests.py --type integration # Run integration database tests
  python run_database_tests.py --type migrations  # Run migration tests
  python run_database_tests.py --benchmark        # Run performance benchmarks
  python run_database_tests.py --schema           # Run schema validation
  python run_database_tests.py --stress           # Run stress tests
  python run_database_tests.py --report           # Generate comprehensive report
        """
    )
    
    parser.add_argument(
        '--type', 
        choices=['all', 'unit', 'integration', 'migrations', 'performance', 'schema', 'integrity'],
        default='all',
        help='Type of database tests to run (default: all)'
    )
    
    parser.add_argument(
        '--no-coverage',
        action='store_true',
        help='Disable coverage reporting'
    )
    
    parser.add_argument(
        '--no-html',
        action='store_true', 
        help='Disable HTML coverage report'
    )
    
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Verbose output'
    )
    
    parser.add_argument(
        '--benchmark',
        action='store_true',
        help='Run database performance benchmarks'
    )
    
    parser.add_argument(
        '--schema',
        action='store_true',
        help='Run database schema validation tests'
    )
    
    parser.add_argument(
        '--stress',
        action='store_true',
        help='Run database stress tests'
    )
    
    parser.add_argument(
        '--report',
        action='store_true',
        help='Generate comprehensive database test report'
    )
    
    args = parser.parse_args()
    
    # Handle special commands first
    if args.report:
        return generate_database_test_report().returncode
    
    if args.benchmark:
        return run_database_benchmarks().returncode
    
    if args.schema:
        return run_database_schema_validation().returncode
    
    if args.stress:
        return run_database_stress_tests().returncode
    
    # Run regular database tests
    result = run_database_tests(
        test_type=args.type,
        coverage=not args.no_coverage,
        html_report=not args.no_html,
        verbose=args.verbose
    )
    
    return result.returncode


if __name__ == '__main__':
    sys.exit(main())
