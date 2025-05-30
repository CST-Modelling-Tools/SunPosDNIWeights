from typing import Dict, Tuple, Callable
from scipy.optimize import differential_evolution
import numpy as np

from optimizers.metaheuristic_optimizer import MetaheuristicOptimizer


class DEBlackBoxOptimizer(MetaheuristicOptimizer):
    """
    Differential Evolution optimizer using SciPy to optimize a black-box function.
    """

    def __init__(
        self,
        parameter_bounds: Dict[str, Tuple[float, float]],
        max_iterations: int,
        population_size: int = 15,
        mutation: float = 0.5,
        recombination: float = 0.7,
        seed: int = None
    ):
        """
        Initialize the optimizer.

        Args:
            parameter_bounds (dict): Dictionary of parameter names to (min, max) tuples.
            max_iterations (int): Maximum number of generations to evolve.
            population_size (int): Number of individuals in the population.
            mutation (float): Differential weight.
            recombination (float): Crossover probability.
            seed (int): Random seed for reproducibility.
        """
        super().__init__(parameter_bounds, max_iterations)
        self.population_size = population_size
        self.mutation = mutation
        self.recombination = recombination
        self.seed = seed

    def optimize(self, objective_function: Callable[[Dict[str, float]], float]) -> Tuple[Dict[str, float], float]:
        """
        Run the DE optimization on the provided objective function.

        Args:
            objective_function (Callable): A function that takes a dict of named parameters and returns a scalar result.

        Returns:
            Tuple[Dict[str, float], float]: Best parameters and best objective value found.
        """

        # Prepare ordered bounds list
        bounds_list = list(self.parameter_bounds.values())
        param_names = list(self.parameter_bounds.keys())

        def wrapped_objective(x):
            param_dict = {name: val for name, val in zip(param_names, x)}
            return -objective_function(param_dict)  # Negate if we want to maximize

        result = differential_evolution(
            func=wrapped_objective,
            bounds=bounds_list,
            maxiter=self.max_iterations,
            popsize=self.population_size,
            mutation=self.mutation,
            recombination=self.recombination,
            seed=self.seed,
            polish=True
        )

        best_params = {name: val for name, val in zip(param_names, result.x)}
        best_value = -result.fun  # Negated back to original

        return best_params, best_value