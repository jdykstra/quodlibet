import serial
import time


class PowerController:
    """Interface to the external power controller via serial communication."""

    def __init__(self, port: str = "/dev/ttyACM0", baudrate: int = 9600, timeout: float = 1.0):
        """
        Initialize the power controller.

        Args:
            port: Serial port device path
            baudrate: Serial communication baud rate
            timeout: Serial read timeout in seconds
        """
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self._serial = None

    def _connect(self):
        """Establish serial connection if not already connected."""
        if self._serial is None or not self._serial.is_open:
            try:
                self._serial = serial.Serial(
                    port=self.port,
                    baudrate=self.baudrate,
                    timeout=self.timeout
                )
                time.sleep(0.1)  # Allow time for connection to stabilize
            except serial.SerialException as e:
                raise ConnectionError(f"Failed to connect to power controller on {self.port}: {e}")

    def _disconnect(self):
        """Close serial connection."""
        if self._serial and self._serial.is_open:
            self._serial.close()

    def _send_command(self, command: str) -> str:
        """
        Send a command to the power controller and return the response.

        Args:
            command: Command string to send

        Returns:
            Response string from the controller

        Raises:
            ConnectionError: If serial communication fails
            ValueError: If command format is invalid
        """
        if not command or len(command.split()) != 2:
            raise ValueError("Command must be in format 'device state'")

        device, state = command.split()
        if device not in ["system", "refrigerator"]:
            raise ValueError("Device must be 'system' or 'refrigerator'")
        if state not in ["on", "off"]:
            raise ValueError("State must be 'on' or 'off'")

        self._connect()
        assert self._serial is not None, "Serial connection failed"

        try:
            # Send command with newline
            self._serial.write(f"{command}\n".encode())
            self._serial.flush()

            # Read response
            response = self._serial.readline().decode().strip()

            if response not in ["OK", "ERR"]:
                raise ValueError(f"Unexpected response from power controller: {response}")

            return response

        except serial.SerialException as e:
            raise ConnectionError(f"Serial communication error: {e}")

    def set_system_power(self, state: str) -> bool:
        """
        Set system power state.

        Args:
            state: "on" or "off"

        Returns:
            True if command was successful, False otherwise
        """
        if state not in ["on", "off"]:
            raise ValueError("State must be 'on' or 'off'")
        response = self._send_command(f"set system {state}")
        return response == "OK"

    def set_refrigerator_power(self, state: str) -> bool:
        """
        Set refrigerator power state.

        Args:
            state: "on" or "off"

        Returns:
            True if command was successful, False otherwise
        """
        if state not in ["on", "off"]:
            raise ValueError("State must be 'on' or 'off'")
        response = self._send_command(f"setrefrigerator {state}")
        return response == "OK"

    def get_system_status(self) -> str:
        """Get current system power status. Note: This may not be implemented by hardware."""
        # This would require a status query command if supported by the hardware
        raise NotImplementedError("Status queries not implemented")

    def get_refrigerator_status(self) -> str:
        """Get current refrigerator power status. Note: This may not be implemented by hardware."""
        # This would require a status query command if supported by the hardware
        raise NotImplementedError("Status queries not implemented")

    def close(self):
        """Clean up and close the serial connection."""
        self._disconnect()


# Create the singleton controller
POWER_CONTROLLER_PORT = "/dev/ttyACM0"  # Adjust as necessary
power_controller = PowerController(port=POWER_CONTROLLER_PORT)