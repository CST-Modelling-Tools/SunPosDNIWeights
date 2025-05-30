from abc import ABC, abstractmethod
from typing import Any, Dict, Tuple

class MetaheuristicOptimizer(ABC):
    """
    Abstract base class for all metaheuristic optimizers.
    """

    def __init__(self, parameter_bounds: Dict[str, Tuple[float, float]], max_iterations: int):
        """
        Initialize the optimizer.

        Args:
            parameter_bounds (dict): Dictionary of parameter names and their (min, max) bounds.
            max_iterations (int): Maximum number of optimization iterations.
        """
        self.parameter_bounds = parameter_bounds
        self.max_iterations = max_iterations

    @abstractmethod
    def suggest(self) -> Dict[str, float]:
        """
        Suggest the next set of parameters to evaluate.

        Returns:
            dict: A dictionary of parameter values.
        """
        pass

    @abstractmethod
    def update(self, parameters: Dict[str, float], result: float) -> None:
        """
        Update the optimizer with the result from a completed evaluation.

        Args:
            parameters (dict): The input parameters that were evaluated.
            result (float): The result of the evaluation (e.g., annual energy).
        """
        pass

    @abstractmethod
    def is_done(self) -> bool:
        """
        Check if the optimization process is finished.

        Returns:
            bool: True if done, False otherwise.
        """
        pass