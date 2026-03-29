"""
Test runner for all KnowHow feature tests.

Usage:
    python run_knowhow_tests.py           # run all KnowHow tests
    python run_knowhow_tests.py -v        # verbose output
    python run_knowhow_tests.py --no-cov  # skip coverage
    python run_knowhow_tests.py -k search # filter by name (e.g. a single feature)

KnowHow test files:
    Feature 1  — Search                 test_knowhow_search.py
    Feature 2  — Article Summary        test_knowhow_summary.py
    Feature 3  — Bookmarks              test_knowhow_bookmarks.py
    Feature 4  — Tags                   test_knowhow_tags.py
    Feature 5  — Draft / Publish        test_knowhow_draft_step1-5.py
    Feature 6  — Reactions              test_knowhow_reactions.py
    Feature 7  — Related Articles       test_knowhow_related_articles.py
    Feature 9  — Category Description   test_knowhow_category_description.py
    Feature 10 — Print / PDF            test_knowhow_print.py
    Feature 12 — New Since Last Visit   test_knowhow_last_visit.py
"""
import sys
import argparse
import subprocess
from pathlib import Path

# All KnowHow test files, in feature order
KNOWHOW_TEST_FILES = [
    'tests/unit/test_knowhow_search.py',
    'tests/unit/test_knowhow_summary.py',
    'tests/unit/test_knowhow_bookmarks.py',
    'tests/unit/test_knowhow_tags.py',
    'tests/unit/test_knowhow_draft_step1.py',
    'tests/unit/test_knowhow_draft_step2.py',
    'tests/unit/test_knowhow_draft_step3.py',
    'tests/unit/test_knowhow_draft_step4.py',
    'tests/unit/test_knowhow_draft_step5.py',
    'tests/unit/test_knowhow_reactions.py',
    'tests/unit/test_knowhow_related_articles.py',
    'tests/unit/test_knowhow_category_description.py',
    'tests/unit/test_knowhow_print.py',
    'tests/unit/test_knowhow_last_visit.py',
]


def build_command(verbose: bool, no_cov: bool, extra: list[str]) -> list[str]:
    cmd = [sys.executable, '-m', 'pytest'] + KNOWHOW_TEST_FILES

    if not no_cov:
        cmd += ['--cov=app', '--cov-report=term-missing']

    if verbose:
        cmd.append('-v')

    cmd += ['--tb=short', '--strict-markers', '--disable-warnings']
    cmd += extra
    return cmd


def main() -> int:
    parser = argparse.ArgumentParser(description='Run all KnowHow feature tests.')
    parser.add_argument('-v', '--verbose', action='store_true',
                        help='Show each test name as it runs')
    parser.add_argument('--no-cov', action='store_true',
                        help='Skip coverage reporting')
    parser.add_argument('-k', metavar='EXPR',
                        help='Only run tests matching this expression (passed to pytest -k)')
    args, remainder = parser.parse_known_args()

    extra = remainder[:]
    if args.k:
        extra += ['-k', args.k]

    # Verify all test files exist
    root = Path(__file__).parent
    missing = [f for f in KNOWHOW_TEST_FILES if not (root / f).exists()]
    if missing:
        print('ERROR: the following test files were not found:')
        for f in missing:
            print(f'  {f}')
        return 1

    cmd = build_command(verbose=args.verbose, no_cov=args.no_cov, extra=extra)
    print('Running:', ' '.join(cmd))
    print()

    try:
        result = subprocess.run(cmd, check=False)
        return result.returncode
    except KeyboardInterrupt:
        print('\nInterrupted.')
        return 1


if __name__ == '__main__':
    sys.exit(main())
