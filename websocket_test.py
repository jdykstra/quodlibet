import random
import time
from camilladsp import CamillaClient

def main():
    # Replace with the correct host and port for your CamillaDSP instance
    host = "127.0.0.1"
    port = 1234

    # Create a CamillaClient instance and connect
    client = CamillaClient(host, port)
    try:
        client.connect()
        print("Connected to CamillaDSP")

        while True:
            # Generate a random volume between -50 and 0 dB
            random_volume = random.uniform(-50, 0)
            print(f"Setting volume to: {random_volume:.2f} dB")

            # Set the main volume
            client.volume.set_main_volume(random_volume)

            # Wait for 1 second
            time.sleep(1)

    except KeyboardInterrupt:
        print("\nExiting...")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        client.disconnect()
        print("Disconnected from CamillaDSP")

if __name__ == "__main__":
    main()