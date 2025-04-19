#!/usr/bin/env python3
"""
Test runner script for AdaptiveCV backend.
Run this script to execute all tests with proper configuration.
"""
import os
import sys
import unittest
import pytest

def setup_test_environment():
    """Setup necessary environment variables for testing"""
    # Use test database
    os.environ["DATABASE_URL"] = "sqlite:///test_adaptive_cv.db"
    # Use mock API key for OpenAI
    os.environ["OPENAI_API_KEY"] = "sk-test-12345"
    # Disable actual API calls
    os.environ["TEST_MODE"] = "true"

def run_all_tests():
    """Run all tests using pytest"""
    setup_test_environment()
    test_dir = os.path.dirname(os.path.abspath(__file__))
    exit_code = pytest.main([
        test_dir,
        "-v", 
        "--no-header",
    ])
    return exit_code

def run_specific_test(test_name=None):
    """Run a specific test or test file"""
    setup_test_environment()
    test_path = os.path.dirname(os.path.abspath(__file__))
    
    if test_name:
        if not test_name.startswith("test_"):
            test_name = f"test_{test_name}"
        if not test_name.endswith(".py"):
            test_name = f"{test_name}.py"
        test_path = os.path.join(test_path, test_name)
    
    exit_code = pytest.main([
        test_path,
        "-v",
        "--no-header",
    ])
    return exit_code

if __name__ == "__main__":
    if len(sys.argv) > 1:
        # If a specific test is provided
        test_name = sys.argv[1]
        sys.exit(run_specific_test(test_name))
    else:
        # Run all tests
        sys.exit(run_all_tests())