"""
Mock modules for testing CircuitPython code on host machine
"""
import gc as _gc


# Mock gc module functions (CircuitPython has additional attributes)
def mock_gc_collect():
    """Mock gc.collect()"""
    return _gc.collect()


def mock_gc_mem_free():
    """Mock memory free - returns a reasonable value for testing"""
    return 100000  # 100KB free


def mock_gc_mem_alloc():
    """Mock memory allocated"""
    return 50000  # 50KB allocated


# Mock board module
class MockBoard:
    """Mock for CircuitPython board module"""

    class MockPin:
        def __init__(self, name):
            self.name = name

        def __repr__(self):
            return f"Pin({self.name})"

    # Common pins
    D0 = MockPin("D0")
    D1 = MockPin("D1")
    A0 = MockPin("A0")
    A1 = MockPin("A1")
    LED = MockPin("LED")


# Mock digitalio module
class MockDigitalIO:
    """Mock for CircuitPython digitalio module"""

    class DigitalInOut:
        def __init__(self, pin):
            self.pin = pin
            self.direction = None
            self.value = False

        def switch_to_output(self, value=False):
            self.direction = "output"
            self.value = value

        def switch_to_input(self, pull=None):
            self.direction = "input"

        def deinit(self):
            pass

    class Direction:
        INPUT = "input"
        OUTPUT = "output"

    class Pull:
        UP = "up"
        DOWN = "down"


# Mock storage module
class MockStorage:
    """Mock for CircuitPython storage module"""

    @staticmethod
    def getmount(path):
        class MockMount:
            def __init__(self):
                self.label = "CIRCUITPY"
        return MockMount()

    @staticmethod
    def remount(path, readonly):
        pass


# Mock audiocore module
class MockAudioCore:
    """Mock for CircuitPython audiocore module"""

    class RawSample:
        def __init__(self, buffer, channel_count=1, sample_rate=22050):
            self.buffer = buffer
            self.channel_count = channel_count
            self.sample_rate = sample_rate
            self.sample_count = len(buffer) // channel_count

        def deinit(self):
            pass


# Mock audiobusio module
class MockAudioBusIO:
    """Mock for CircuitPython audiobusio module"""

    class I2SOut:
        def __init__(self, bit_clock, word_select, data):
            self.bit_clock = bit_clock
            self.word_select = word_select
            self.data = data
            self.playing = False

        def play(self, sample, loop=False):
            self.playing = True

        def stop(self):
            self.playing = False

        def deinit(self):
            self.playing = False


# Function to inject mocks
def inject_mocks():
    """Inject mock modules into sys.modules for testing"""
    import sys
    from types import ModuleType

    # Create a proper module for gc
    gc_module = ModuleType('gc')
    gc_module.collect = mock_gc_collect
    gc_module.mem_free = mock_gc_mem_free
    gc_module.mem_alloc = mock_gc_mem_alloc
    sys.modules['gc'] = gc_module

    sys.modules['board'] = MockBoard()
    sys.modules['digitalio'] = MockDigitalIO()
    sys.modules['storage'] = MockStorage()
    sys.modules['audiocore'] = MockAudioCore()
    sys.modules['audiobusio'] = MockAudioBusIO()


# Check if we're running on CircuitPython or need mocks
def setup_test_environment():
    """Setup test environment with mocks if needed"""
    try:
        import board
        # If this succeeds, we're on CircuitPython hardware
        return False
    except ImportError:
        # We're on a host machine, inject mocks
        inject_mocks()
        return True
