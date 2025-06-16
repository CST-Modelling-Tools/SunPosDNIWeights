import math
from optimizers.differential_evolution_optimizer import DifferentialEvolutionOptimizer

def test_de_optimizer_basic_flow():
    bounds = {
        "a0": [5.0, 20.0],
        "b": [0.5, 5.0],
        "delta": [0.0, 2 * math.pi]
    }

    optimizer = DifferentialEvolutionOptimizer(
        bounds=bounds,
        population_size=5,
        max_generations=3,
        mutation_factor=0.8,
        crossover_rate=0.9
    )

    # Initial population
    initial = optimizer.suggest()
    assert len(initial) == 5
    for params in initial:
        for key in bounds:
            assert bounds[key][0] <= params[key] <= bounds[key][1]

    # Simulate fake fitness update
    evaluated = []
    for i, p in enumerate(initial):
        p_with_fitness = p.copy()
        p_with_fitness["fitness"] = float(i)
        evaluated.append(p_with_fitness)

    optimizer.update(evaluated)
    assert not optimizer.is_done()

    # Suggest next generation
    next_gen = optimizer.suggest()
    assert len(next_gen) == 5

    # Update again with new fake fitnesses
    for i, p in enumerate(next_gen):
        p["fitness"] = float(i + 1)
    optimizer.update(next_gen)

    assert not optimizer.is_done()
    optimizer.update(next_gen)
    assert optimizer.is_done()