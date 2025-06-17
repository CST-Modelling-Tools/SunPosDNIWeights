# File: optimization/population_generator.py

import numpy as np
from typing import List, Tuple

def generate_initial_population(
    population_size: int,
    parameter_bounds: List[Tuple[float, float]],
    seed: int = None
) -> np.ndarray:
    """
    Generates an initial population for the DE optimizer.

    Parameters:
        population_size: Number of parameter sets to generate.
        parameter_bounds: A list of (min, max) tuples for each parameter.
        seed: Optional seed for reproducibility.

    Returns:
        A NumPy array of shape (population_size, num_parameters)
        where each row is a parameter set.
    """
    if seed is not None:
        np.random.seed(seed)

    num_params = len(parameter_bounds)
    population = np.empty((population_size, num_params))

    for i, (low, high) in enumerate(parameter_bounds):
        population[:, i] = np.random.uniform(low, high, population_size)

    return population