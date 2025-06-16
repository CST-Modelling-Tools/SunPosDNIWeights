from abc import ABC, abstractmethod
from typing import List, Dict

class MetaheuristicOptimizer(ABC):
    """
    Abstract base class for any metaheuristic optimizer.
    """

    @abstractmethod
    def suggest(self) -> List[Dict]:
        """
        Suggest a list of new candidate solutions (parameter sets) for the next generation.
        """
        pass

    @abstractmethod
    def update(self, evaluated_population: List[Dict]):
        """
        Update the internal state of the optimizer based on the evaluated fitnesses.
        Each element must contain both parameters and a 'fitness' field.
        """
        pass

    @abstractmethod
    def is_done(self) -> bool:
        """
        Determine if the optimization process should stop.
        """
        pass