import unittest
import sys
import os

# Add the project root to the path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(project_root, '..', 'src'))

def run_tests(test_module=None):
    """Run tests with optional module filter"""
    if test_module:
        # Run specific test module
        loader = unittest.TestLoader()
        suite = loader.loadTestsFromName(test_module)
    else:
        # Discover and run all tests
        loader = unittest.TestLoader()
        start_dir = os.path.dirname(os.path.abspath(__file__))
        suite = loader.discover(start_dir, pattern='test_*.py')
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Return exit code based on test results
    return 0 if result.wasSuccessful() else 1

if __name__ == '__main__':
    test_module = sys.argv[1] if len(sys.argv) > 1 else None
    exit_code = run_tests(test_module)
    sys.exit(exit_code)
