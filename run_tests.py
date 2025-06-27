#!/usr/bin/env python3
"""
Test runner script for PDF to JSON converter
Executes all unit tests and provides detailed reporting
"""

import sys
import os
import unittest
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def run_tests():
    """Run all tests and return results"""
    # Discover and run tests
    loader = unittest.TestLoader()
    start_dir = project_root / 'tests'
    suite = loader.discover(start_dir, pattern='test_*.py')
    
    # Run tests with detailed output
    runner = unittest.TextTestRunner(verbosity=2, stream=sys.stdout)
    result = runner.run(suite)
    
    return result

def print_summary(result):
    """Print detailed test summary"""
    print("\n" + "="*60)
    print("TEST EXECUTION SUMMARY")
    print("="*60)
    print(f"Total tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Skipped: {len(result.skipped) if hasattr(result, 'skipped') else 0}")
    
    # Calculate success rate
    total_issues = len(result.failures) + len(result.errors)
    success_rate = ((result.testsRun - total_issues) / result.testsRun * 100) if result.testsRun > 0 else 0
    print(f"Success rate: {success_rate:.1f}%")
    
    # Print failures
    if result.failures:
        print(f"\n{'='*60}")
        print("FAILURES:")
        print("="*60)
        for test, traceback in result.failures:
            print(f"\nTest: {test}")
            print(f"Traceback:\n{traceback}")
    
    # Print errors
    if result.errors:
        print(f"\n{'='*60}")
        print("ERRORS:")
        print("="*60)
        for test, traceback in result.errors:
            print(f"\nTest: {test}")
            print(f"Traceback:\n{traceback}")
    
    print("\n" + "="*60)
    
    # Return appropriate exit code
    return 0 if total_issues == 0 else 1

def main():
    """Main function to run tests"""
    print("Running PDF to JSON Converter Tests")
    print("="*60)
    
    try:
        result = run_tests()
        exit_code = print_summary(result)
        sys.exit(exit_code)
    except Exception as e:
        print(f"Error running tests: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main() 