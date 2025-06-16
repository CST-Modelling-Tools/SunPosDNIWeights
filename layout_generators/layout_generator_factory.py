from layout_generators.layout_generator_biomimetic_spiral import BiomimeticSpiralGenerator

def get_layout_generator(generator_type: str):
    """
    Returns the layout generator class (not an instance) based on the given type.

    Args:
        generator_type (str): The layout generator type (e.g., "biomimetic_spiral")

    Returns:
        A class that can be instantiated with (num_heliostats, bubble_radius, receiver_height)
    """
    generator_type = generator_type.lower()

    if generator_type == "biomimetic_spiral":
        return BiomimeticSpiralGenerator
    else:
        raise ValueError(f"Unknown layout generator type: {generator_type}")