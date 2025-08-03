"""
Test runner script for PanelMerge application
"""
import os
import sys
import subprocess
import argparse
from pathlib import Path


def run_tests(test_type='all', coverage=True, html_report=False, verbose=False):
    """Run tests with specified options."""
    
    # Base pytest command
    cmd = ['python', '-m', 'pytest']
    
    # Add test path based on type
    if test_type == 'unit':
        cmd.append('tests/unit/')
    elif test_type == 'integration':
        cmd.append('tests/integration/')
    elif test_type == 'database':
        cmd.extend(['-m', 'database'])
    elif test_type == 'all':
        cmd.append('tests/')
    else:
        cmd.append(f'tests/{test_type}')
    
    # Add coverage options
    if coverage:
        cmd.extend(['--cov=app', '--cov-report=term-missing'])
        if html_report:
            cmd.append('--cov-report=html')
    
    # Add verbosity
    if verbose:
        cmd.append('-v')
    
    # Add other useful options
    cmd.extend([
        '--tb=short',
        '--strict-markers',
        '--disable-warnings'
    ])
    
    print(f"Running command: {' '.join(cmd)}")
    
    # Run the tests
    try:
        result = subprocess.run(cmd, check=False)
        return result.returncode
    except KeyboardInterrupt:
        print("\nTests interrupted by user")
        return 1
    except Exception as e:
        print(f"Error running tests: {e}")
        return 1


def run_database_tests(db_test_type='all', coverage=True, html_report=False, verbose=False):
    """Run database-specific tests."""
    
    cmd = ['python', '-m', 'pytest']
    
    # Database test selection
    if db_test_type == 'unit':
        cmd.extend(['-m', 'unit and database'])
    elif db_test_type == 'integration':
        cmd.extend(['-m', 'integration and database']) 
    elif db_test_type == 'migrations':
        cmd.append('tests/unit/test_database_migrations.py')
    elif db_test_type == 'performance':
        cmd.extend(['-m', 'database and slow'])
    else:  # 'all'
        cmd.extend(['-m', 'database'])
    
    # Coverage specific to database components
    if coverage:
        cmd.extend([
            '--cov=app.models',
            '--cov=app.extensions',
            '--cov-report=term-missing'
        ])
        if html_report:
            cmd.append('--cov-report=html:htmlcov/database')
    
    if verbose:
        cmd.append('-v')
    
    cmd.extend(['--tb=short', '--disable-warnings'])
    
    print(f"Running database tests: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, check=False)
        return result.returncode
    except KeyboardInterrupt:
        print("\nDatabase tests interrupted by user")
        return 1
    except Exception as e:
        print(f"Error running database tests: {e}")
        return 1
    """Run specific tests based on markers or patterns."""
    
    cmd = ['python', '-m', 'pytest']
    
    # Add marker filtering
    if markers:
        for marker in markers:
            cmd.extend(['-m', marker])
    
    # Add file pattern
    if file_pattern:
        cmd.extend(['-k', file_pattern])
    
    # Add function pattern
    if function_pattern:
        cmd.extend(['-k', function_pattern])
    
    cmd.extend(['-v', '--tb=short'])
    
    print(f"Running command: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, check=False)
        return result.returncode
    except KeyboardInterrupt:
        print("\nTests interrupted by user")
        return 1


def run_specific_tests(markers=None, file_pattern=None, function_pattern=None):
    """Run specific tests based on markers or patterns."""
    
    cmd = ['python', '-m', 'pytest']
    
    # Add marker filtering
    if markers:
        marker_expr = ' and '.join(markers)
        cmd.extend(['-m', marker_expr])
    
    # Add file pattern
    if file_pattern:
        cmd.extend(['-k', file_pattern])
    
    # Add function pattern
    if function_pattern:
        cmd.extend(['-k', function_pattern])
    
    cmd.extend(['-v', '--tb=short'])
    
    print(f"Running command: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, check=False)
        return result.returncode
    except KeyboardInterrupt:
        print("\nTests interrupted by user")
        return 1
    """Set up the test environment."""
    
    print("Setting up test environment...")
    
    # Set environment variables for testing
    os.environ['FLASK_ENV'] = 'testing'
    os.environ['TESTING'] = 'True'
    
    # Create test directories if they don't exist
    test_dirs = ['tests', 'tests/unit', 'tests/integration', 'tests/fixtures']
    for test_dir in test_dirs:
        Path(test_dir).mkdir(exist_ok=True)
    
    print("Test environment setup complete.")


def setup_test_environment():
    """Set up the test environment."""
    
    print("Setting up test environment...")
    
    # Set environment variables for testing
    os.environ['FLASK_ENV'] = 'testing'
    os.environ['TESTING'] = 'True'
    
    # Create test directories if they don't exist
    test_dirs = ['tests', 'tests/unit', 'tests/integration', 'tests/fixtures']
    for test_dir in test_dirs:
        Path(test_dir).mkdir(exist_ok=True)
    
    print("Test environment setup complete.")
    """Install test dependencies."""
    
    print("Installing test dependencies...")
    
    dependencies = [
        'pytest>=7.4.0',
        'pytest-flask>=1.2.0',
        'pytest-cov>=4.1.0',
        'pytest-mock>=3.11.0',
        'pytest-html>=3.2.0',
        'coverage>=7.2.0',
        'factory-boy>=3.3.0',
        'freezegun>=1.2.0',
        'responses>=0.23.0'
    ]
    
    for dep in dependencies:
        try:
            subprocess.run(['pip', 'install', dep], check=True)
            print(f"✅ Installed {dep}")
        except subprocess.CalledProcessError:
            print(f"❌ Failed to install {dep}")
    
    print("Test dependencies installation complete.")


def generate_test_report():
    """Generate comprehensive test report."""
    
    print("Generating comprehensive test report...")
    
    # Run tests with detailed reporting
    cmd = [
        'python', '-m', 'pytest',
        'tests/',
        '--cov=app',
        '--cov-report=html:htmlcov',
        '--cov-report=xml',
        '--cov-report=term-missing',
        '--html=report.html',
        '--self-contained-html',
        '-v'
    ]
    
    try:
        result = subprocess.run(cmd, check=False)
        
        if result.returncode == 0:
            print("\n✅ Test report generated successfully!")
            print("📊 Coverage report: htmlcov/index.html")
            print("📋 Test report: report.html")
        else:
            print(f"\n❌ Tests failed with return code {result.returncode}")
        
        return result.returncode
        
    except Exception as e:
        print(f"Error generating report: {e}")
        return 1


def main():
    """Main test runner function."""
    
    parser = argparse.ArgumentParser(description='PanelMerge Test Runner')
    parser.add_argument('--type', choices=['unit', 'integration', 'all', 'database'], 
                       default='all', help='Type of tests to run')
    parser.add_argument('--coverage', action='store_true', default=True,
                       help='Include coverage reporting')
    parser.add_argument('--html', action='store_true',
                       help='Generate HTML coverage report')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Verbose output')
    parser.add_argument('--markers', nargs='+',
                       help='Run tests with specific markers (e.g., database, cache, auth)')
    parser.add_argument('--pattern', 
                       help='Run tests matching pattern')
    parser.add_argument('--setup', action='store_true',
                       help='Set up test environment')
    parser.add_argument('--install-deps', action='store_true',
                       help='Install test dependencies')
    parser.add_argument('--report', action='store_true',
                       help='Generate comprehensive test report')
    parser.add_argument('--database', action='store_true',
                       help='Run database-specific tests')
    parser.add_argument('--database-type', 
                       choices=['unit', 'integration', 'migrations', 'performance', 'all'],
                       default='all',
                       help='Type of database tests to run')
    
    args = parser.parse_args()
    
    # Handle special commands
    if args.setup:
        setup_test_environment()
        return 0
    
    if args.install_deps:
        install_test_dependencies()
        return 0
    
    if args.report:
        return generate_test_report()
    
    # Handle database tests
    if args.database or args.type == 'database':
        return run_database_tests(
            db_test_type=args.database_type,
            coverage=args.coverage,
            html_report=args.html,
            verbose=args.verbose
        )
    
    # Run specific tests based on markers or patterns
    if args.markers or args.pattern:
        return run_specific_tests(
            markers=args.markers,
            file_pattern=args.pattern
        )
    
    # Run regular tests
    return run_tests(
        test_type=args.type,
        coverage=args.coverage,
        html_report=args.html,
        verbose=args.verbose
    )


if __name__ == '__main__':
    sys.exit(main())
