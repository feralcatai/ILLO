import serial
import serial.tools.list_ports
import time
import threading
import sys

class CircuitPlaygroundSerial:
    def __init__(self, port=None, baudrate=115200):
        self.port = port
        self.baudrate = baudrate
        self.serial_connection = None
        self.running = False

    def find_circuitpython_ports(self):
        """Find all CircuitPython device ports"""
        ports = serial.tools.list_ports.comports()
        circuitpython_ports = []
        for port in ports:
            # CircuitPython devices typically show up with these identifiers
            if any(identifier in port.description.lower() for identifier in
                   ['circuitpython', 'circuit playground', 'adafruit']):
                circuitpython_ports.append(port)
        return circuitpython_ports

    def select_port(self):
        """Interactively select a port from available options"""
        cp_ports = self.find_circuitpython_ports()

        if not cp_ports:
            print("No CircuitPython devices found.")
            # Show all available ports as fallback
            all_ports = list(serial.tools.list_ports.comports())
            if not all_ports:
                print("No serial ports available on this system.")
                return None

            print("\nAvailable serial ports:")
            for idx, port in enumerate(all_ports, 1):
                print(f"  {idx}. {port.device} - {port.description}")

            try:
                choice = input("\nSelect port number (or 'q' to quit): ").strip()
                if choice.lower() == 'q':
                    return None
                port_idx = int(choice) - 1
                if 0 <= port_idx < len(all_ports):
                    return all_ports[port_idx].device
                else:
                    print("Invalid selection")
                    return None
            except (ValueError, KeyboardInterrupt):
                return None

        elif len(cp_ports) == 1:
            # Auto-select if only one CircuitPython device found
            selected = cp_ports[0]
            print(f"Found CircuitPython device: {selected.device} - {selected.description}")
            return selected.device

        else:
            # Multiple CircuitPython devices found, let user choose
            print("Multiple CircuitPython devices found:")
            for idx, port in enumerate(cp_ports, 1):
                print(f"  {idx}. {port.device} - {port.description}")

            try:
                choice = input("\nSelect port number (or 'q' to quit): ").strip()
                if choice.lower() == 'q':
                    return None
                port_idx = int(choice) - 1
                if 0 <= port_idx < len(cp_ports):
                    return cp_ports[port_idx].device
                else:
                    print("Invalid selection")
                    return None
            except (ValueError, KeyboardInterrupt):
                return None
    
    def connect(self):
        """Connect to the Circuit Playground"""
        try:
            # Auto-select port if not specified
            if not self.port:
                self.port = self.select_port()
                if not self.port:
                    print("No port selected")
                    return False

            self.serial_connection = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                timeout=0.1,
                write_timeout=1
            )
            print(f"\nConnected to {self.port} at {self.baudrate} baud")
            return True

        except serial.SerialException as e:
            print(f"Failed to connect to {self.port}: {e}")
            return False
    
    def start_monitoring(self):
        """Start monitoring serial output"""
        if not self.connect():
            return
            
        self.running = True
        
        def read_serial():
            while self.running:
                try:
                    if self.serial_connection and self.serial_connection.in_waiting > 0:
                        line = self.serial_connection.readline().decode('utf-8', errors='ignore').strip()
                        if line:
                            print(f"[{time.strftime('%H:%M:%S')}] {line}")
                except serial.SerialException as e:
                    print(f"Serial read error: {e}")
                    break
                except UnicodeDecodeError:
                    # Skip lines that can't be decoded
                    pass
                time.sleep(0.01)
        
        # Start reading in a separate thread
        read_thread = threading.Thread(target=read_serial, daemon=True)
        read_thread.start()
        
        print("Serial monitor started. Press Ctrl+C to stop, or type commands:")
        
        try:
            while self.running:
                # Allow sending commands to the device
                user_input = input()
                if user_input.lower() in ['exit', 'quit', 'stop']:
                    break
                elif user_input and self.serial_connection:
                    # Send command to Circuit Playground (triggers REPL if needed)
                    self.serial_connection.write((user_input + '\r\n').encode())
                    
        except KeyboardInterrupt:
            print("\nStopping serial monitor...")
        finally:
            self.stop()
    
    def stop(self):
        """Stop the serial connection"""
        self.running = False
        if self.serial_connection:
            self.serial_connection.close()
            print("Serial connection closed")

def main():
    """
    Main entry point for the serial monitor.

    Usage:
        python serial_monitor.py              # Auto-detect and select port
        python serial_monitor.py COM7         # Use specific port
    """
    port = None
    if len(sys.argv) > 1:
        # Port specified as command line argument
        port = sys.argv[1]
        print(f"Using specified port: {port}")

    monitor = CircuitPlaygroundSerial(port=port, baudrate=115200)
    monitor.start_monitoring()

if __name__ == "__main__":
    main()
