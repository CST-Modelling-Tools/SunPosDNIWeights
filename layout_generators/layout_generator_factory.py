# File: layout_generators/layout_generator_factory.py

from layout_generators.layout_generator_biomimetic_spiral import BiomimeticSpiralGenerator
from layout_generators.layout_generator_octagon_biomimetic_spiral import OctagonBiomimeticSpiralGenerator
from layout_generators.layout_generator_radial_staggered import RadialStaggeredGenerator


# Centralized registry of available generator classes
_LAYOUT_GENERATORS = {
    "biomimetic_spiral": BiomimeticSpiralGenerator,
    "octagon_biomimetic_spiral": OctagonBiomimeticSpiralGenerator,
    "radial_staggered": RadialStaggeredGenerator,
    # Optional aliases for flexibility
    "radial_staggering": RadialStaggeredGenerator,
    "radial_staggered_layout": RadialStaggeredGenerator,
}


def get_layout_generator(generator_type: str):
    """
    Factory function returning a layout generator **class** (not instance)
    based on the specified type.

    Args:
        generator_type (str): Layout generator type (case-insensitive).
            Known options include:
              - "biomimetic_spiral"
              - "octagon_biomimetic_spiral"
              - "radial_staggered"
              (aliases: "radial_staggering", "radial_staggered_layout")

    Returns:
        type: The corresponding generator class, to be instantiated by caller.

    Raises:
        ValueError: If an unknown generator type is provided.
    """
    key = generator_type.strip().lower()
    if key in _LAYOUT_GENERATORS:
        return _LAYOUT_GENERATORS[key]

    valid_keys = ", ".join(sorted(_LAYOUT_GENERATORS.keys()))
    raise ValueError(
        f"Unknown layout generator type: '{generator_type}'. "
        f"Available options: {valid_keys}"
    )