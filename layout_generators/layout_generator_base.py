from abc import ABC, abstractmethod
from pathlib import Path

class ParametricLayoutGenerator(ABC):
    @abstractmethod
    def generate_layout(self, output_file: Path, parameters: dict):
        """
        Generate a heliostat layout CSV file from a given parameter set.

        Args:
            output_file (Path): Path to save the generated CSV file.
            parameters (dict): Dictionary containing generator-specific parameters.
        """
        pass