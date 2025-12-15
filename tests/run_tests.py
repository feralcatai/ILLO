"""
Test runner for CircuitPython project
Runs all unit tests and reports results
"""
import sys
import os
import gc

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from tests.test_framework import TestRunner
from tests.mocks import setup_test_environment

# Setup test environment (will inject mocks if not on CircuitPython)
is_mocked = setup_test_environment()

if is_mocked:
    print("Running in MOCK mode (host machine)")
else:
    print("Running in HARDWARE mode (CircuitPython device)")

# Import test cases
from tests.test_memory_manager import TestMemoryManager
from tests.test_config_manager import TestConfigManager
from tests.test_audio_processor import TestAudioProcessor


def main():
    """Main test runner function"""
    print("\n" + "="*60)
    print("CircuitPython Unit Test Suite")
    print("="*60)

    # Create test runner
    runner = TestRunner()

    # Define test cases to run
    test_cases = [
        TestMemoryManager,
        TestConfigManager,
        TestAudioProcessor,
    ]

    # Run all tests
    success = runner.run(test_cases, verbose=True)

    # Report memory usage
    if hasattr(gc, 'mem_free'):
        print(f"\nMemory after tests: {gc.mem_free()} bytes free")

    # Return exit code
    return 0 if success else 1


if __name__ == '__main__':
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\nTests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nFatal error running tests: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
