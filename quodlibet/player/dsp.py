
import os

from camilladsp import CamillaClient

class DspController(CamillaClient):
    def __init__(self, host: str, port: int):

        super().__init__(host, port)
    
    def get_configs(self) -> tuple:
        """
        Get a set of available configuration filenames and the path to them.
        Maybe in the future this could be a set of dictionaries with more info.
        Returns:
            tuple: A tuple containing the directory path and a set of configuration filenames.
        Raises:
            ValueError: If the current configuration file path is not set.
        """
        current_config_path = self.config.file_path()
        if not current_config_path:
            raise ValueError("No current configuration file path available.")

        config_dir = os.path.dirname(current_config_path)
        yml_files = {file for file in os.listdir(config_dir) if file.endswith('.yml')}

        return config_dir, yml_files

#  Create the singleton controller.
# # ?? Put address and port in the QL configuration file some day.
DSP_HOST = "127.0.0.1"
DSP_PORT = 1234 
dsp_controller = DspController(DSP_HOST, DSP_PORT)

