"""
Minimal test framework for CircuitPython
Designed to work with limited memory constraints
"""
import gc


class TestCase:
    """Base class for test cases"""

    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.errors = []

    def setUp(self):
        """Override this method to set up test fixtures"""
        pass

    def tearDown(self):
        """Override this method to clean up after tests"""
        pass

    def assert_equal(self, actual, expected, msg=None):
        """Assert that two values are equal"""
        if actual != expected:
            error_msg = msg or f"Expected {expected}, got {actual}"
            raise AssertionError(error_msg)

    def assert_true(self, condition, msg=None):
        """Assert that a condition is true"""
        if not condition:
            error_msg = msg or "Expected True"
            raise AssertionError(error_msg)

    def assert_false(self, condition, msg=None):
        """Assert that a condition is false"""
        if condition:
            error_msg = msg or "Expected False"
            raise AssertionError(error_msg)

    def assert_not_none(self, value, msg=None):
        """Assert that value is not None"""
        if value is None:
            error_msg = msg or "Expected not None"
            raise AssertionError(error_msg)

    def assert_raises(self, exception_type, callable_func, *args, **kwargs):
        """Assert that calling a function raises an exception"""
        try:
            callable_func(*args, **kwargs)
            raise AssertionError(f"Expected {exception_type.__name__} to be raised")
        except exception_type:
            pass  # Expected

    def run_test(self, test_method_name):
        """Run a single test method"""
        try:
            self.setUp()
            method = getattr(self, test_method_name)
            method()
            self.tearDown()
            self.passed += 1
            return True, None
        except AssertionError as e:
            self.failed += 1
            error_msg = f"{test_method_name}: {str(e)}"
            self.errors.append(error_msg)
            return False, error_msg
        except Exception as e:
            self.failed += 1
            error_msg = f"{test_method_name}: Unexpected error: {str(e)}"
            self.errors.append(error_msg)
            return False, error_msg
        finally:
            gc.collect()  # Clean up memory after each test

    def run_all_tests(self, verbose=True):
        """Run all test methods (those starting with 'test_')"""
        test_methods = [m for m in dir(self) if m.startswith('test_')]

        if verbose:
            print(f"\n{'='*50}")
            print(f"Running {len(test_methods)} tests in {self.__class__.__name__}")
            print('='*50)

        for test_method in test_methods:
            success, error = self.run_test(test_method)
            if verbose:
                status = "✓ PASS" if success else "✗ FAIL"
                print(f"{status}: {test_method}")
                if error and not success:
                    print(f"  {error}")

        if verbose:
            print(f"\n{'='*50}")
            print(f"Results: {self.passed} passed, {self.failed} failed")
            print('='*50)

        return self.passed, self.failed


class TestRunner:
    """Runner for multiple test cases"""

    def __init__(self):
        self.total_passed = 0
        self.total_failed = 0

    def run(self, test_cases, verbose=True):
        """Run multiple test cases"""
        if verbose:
            print(f"\n{'#'*50}")
            print("# STARTING TEST SUITE")
            print(f"{'#'*50}")

        for test_case_class in test_cases:
            test_case = test_case_class()
            passed, failed = test_case.run_all_tests(verbose=verbose)
            self.total_passed += passed
            self.total_failed += failed
            gc.collect()  # Clean up between test cases

        if verbose:
            print(f"\n{'#'*50}")
            print(f"# TOTAL: {self.total_passed} passed, {self.total_failed} failed")
            print(f"{'#'*50}\n")

        return self.total_failed == 0
