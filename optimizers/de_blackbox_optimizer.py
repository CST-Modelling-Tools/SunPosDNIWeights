from pathlib import Path
from typing import Dict, Tuple, List, Optional
import numpy as np
import random


class DifferentialEvolutionOptimizer:
    """
    A Differential Evolution optimizer compatible with external black-box evaluations.
    It follows the suggest-update-is_done interface.
    """

    def __init__(self,
                 parameter_bounds: Dict[str, Tuple[float, float]],
                 max_generations: int,
                 population_size: int = 8,
                 mutation: float = 0.8,
                 crossover: float = 0.7,
                 seed: Optional[int] = None):

        self.parameter_bounds = parameter_bounds
        self.max_generations = max_generations
        self.population_size = population_size
        self.mutation = mutation
        self.crossover = crossover
        self.seed = seed

        self.param_names = list(parameter_bounds.keys())
        self.dim = len(self.param_names)
        self.bounds_array = np.array([parameter_bounds[k] for k in self.param_names])

        if self.seed is not None:
            np.random.seed(self.seed)
            random.seed(self.seed)

        self.population: List[Dict[str, float]] = []
        self.scores: List[float] = []
        self.generation = 0
        self.current_candidates: List[Dict[str, float]] = []

        self._initialize_population()

    def _initialize_population(self):
        for _ in range(self.population_size):
            vec = [np.random.uniform(low, high) for (low, high) in self.bounds_array]
            self.population.append(dict(zip(self.param_names, vec)))
            self.scores.append(None)

    def suggest(self) -> List[Dict[str, float]]:
        """
        Suggest a batch of parameter sets to evaluate.
        """
        self.current_candidates = []

        for i in range(self.population_size):
            idxs = list(range(self.population_size))
            idxs.remove(i)
            a, b, c = random.sample(idxs, 3)

            xa = np.array([self.population[a][k] for k in self.param_names])
            xb = np.array([self.population[b][k] for k in self.param_names])
            xc = np.array([self.population[c][k] for k in self.param_names])

            mutant = xa + self.mutation * (xb - xc)
            mutant = np.clip(mutant, self.bounds_array[:, 0], self.bounds_array[:, 1])

            trial = np.array([mutant[j] if random.random() < self.crossover else self.population[i][self.param_names[j]]
                              for j in range(self.dim)])

            candidate = dict(zip(self.param_names, trial))
            self.current_candidates.append(candidate)

        return self.current_candidates

    def update(self, parameters: Dict[str, float], result: float) -> None:
        """
        Update the population with the result of a single evaluated candidate.
        """
        for i, cand in enumerate(self.current_candidates):
            if cand == parameters:
                trial_vec = np.array([parameters[k] for k in self.param_names])
                target_vec = np.array([self.population[i][k] for k in self.param_names])
                trial_score = result
                target_score = self.scores[i]

                if target_score is None or trial_score > target_score:
                    self.population[i] = parameters
                    self.scores[i] = trial_score
                break

        # If all candidates are processed, move to next generation
        if all(s is not None for s in self.scores):
            self.generation += 1
            self.current_candidates = []

    def is_done(self) -> bool:
        return self.generation >= self.max_generations

    def best_solution(self) -> Dict[str, float]:
        idx = np.argmax(self.scores)
        return {
            "parameters": self.population[idx],
            "result": self.scores[idx]
        }