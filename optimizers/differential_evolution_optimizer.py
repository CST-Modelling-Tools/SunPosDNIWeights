import random
from typing import List, Dict
from .metaheuristic_optimizer import MetaheuristicOptimizer

class DifferentialEvolutionOptimizer(MetaheuristicOptimizer):
    def __init__(self,
                 bounds: Dict[str, List[float]],
                 population_size: int,
                 mutation_factor: float,
                 crossover_rate: float,
                 max_generations: int):
        self.bounds = bounds
        self.population_size = population_size
        self.mutation_factor = mutation_factor
        self.crossover_rate = crossover_rate
        self.max_generations = max_generations

        self.generation = 0
        self.population = self._initialize_population()
        self.fitnesses = [None] * population_size

    def _initialize_population(self) -> List[Dict]:
        return [
            {key: random.uniform(*self.bounds[key]) for key in self.bounds}
            for _ in range(self.population_size)
        ]

    def suggest(self, generation_id: int) -> List[Dict]:
        if self.generation == 0:
            return self.population  # Initial generation is already initialized

        suggestions = []
        for i in range(self.population_size):
            indices = list(range(self.population_size))
            indices.remove(i)
            a, b, c = random.sample(indices, 3)
            base = self.population[a]
            diff1 = self.population[b]
            diff2 = self.population[c]

            trial = {}
            for key in self.bounds:
                if random.random() < self.crossover_rate:
                    mutated_value = base[key] + self.mutation_factor * (diff1[key] - diff2[key])
                    min_val, max_val = self.bounds[key]
                    trial[key] = max(min_val, min(max_val, mutated_value))
                else:
                    trial[key] = self.population[i][key]

            suggestions.append(trial)

        return suggestions

    def update(self, evaluated_population: List[Dict]):
        for i, candidate in enumerate(evaluated_population):
            new_fitness = candidate["fitness"]
            new_parameters = candidate["parameters"]  # Extract only the parameter dict

            if self.fitnesses[i] is None or new_fitness > self.fitnesses[i]:
                self.population[i] = new_parameters  # Replace with better candidate
                self.fitnesses[i] = new_fitness

        self.generation += 1


    def is_done(self, generation_id=None, max_generations=None) -> bool:
        return self.generation >= self.max_generations