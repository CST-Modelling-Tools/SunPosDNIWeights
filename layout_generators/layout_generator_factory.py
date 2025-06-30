# File: layout_generators/layout_generator_factory.py

from layout_generators.layout_generator_biomimetic_spiral import BiomimeticSpiralGenerator
from layout_generators.layout_generator_octagon_biomimetic_spiral import OctagonBiomimeticSpiralGenerator

def get_layout_generator(generator_type: str):
    """
    Factory function that returns the layout generator class based on the given type.

    Args:
        generator_type (str): The layout generator type (e.g., "biomimetic_spiral" or "octagon_biomimetic_spiral")

    Returns:
        A class that can be instantiated with the appropriate parameters.
    """
    generator_type = generator_type.lower()

    if generator_type == "biomimetic_spiral":
        return BiomimeticSpiralGenerator
    elif generator_type == "octagon_biomimetic_spiral":
        return OctagonBiomimeticSpiralGenerator
    else:
        raise ValueError(f"Unknown layout generator type: {generator_type}")