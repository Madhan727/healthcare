import sys
import os
import unittest
import traceback

# Add root path
sys.path.append(os.getcwd())

from tests.test_refinement import IntegrationRefinementTests

def run_test():
    suite = unittest.TestSuite()
    suite.addTest(IntegrationRefinementTests('test_automated_risk_adjustment'))
    runner = unittest.TextTestRunner(stream=sys.stdout, verbosity=2)
    try:
        runner.run(suite)
    except Exception:
        traceback.print_exc()

if __name__ == '__main__':
    run_test()
