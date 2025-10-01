# File: tests/test_generate_layout_from_parameters.py

import pytest
from pathlib import Path
import csv

from firetasks.generate_layout_from_parameters import GenerateLayoutFromParametersFiretask


class DummyGenerator:
    """A fake generator to replace real heliostat field generators."""
    def __init__(self, **kwargs):
        self.kwargs = kwargs
        self.called = False

    def generate_layout(self, output_file, parameters):
        self.called = True
        # Just write a dummy CSV with parameter keys/values
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["param", "value"])
            for k, v in parameters.items():
                writer.writerow([k, v])


@pytest.fixture
def patch_get_layout_generator(monkeypatch):
    """Patch the layout generator factory to return DummyGenerator."""

    def _fake_get_layout_generator(generator_type):
        return DummyGenerator

    monkeypatch.setattr(
        "firetasks.generate_layout_from_parameters.get_layout_generator",
        _fake_get_layout_generator,
    )


def test_generate_layout_radial_staggered(tmp_path, patch_get_layout_generator):
    output_file = tmp_path / "layout_radial.csv"
    params = {
        "receiver_height": 80.0,
        "flat_receiver_radius": 1.5,
        "flat_receiver_tilt": 0.0,
        "min_tower_clearance": 10.0,
        "north_only": True,
        "d0": 6.0,
        "alpha": 0.1,
        "a0": 0.5,
        "gamma": 0.01,
        "num_heliostats": 6500,
        "bubble_radius": 2.4,
    }

    firetask = GenerateLayoutFromParametersFiretask(
        {
            "generator_type": "radial_staggered",
            "parameters": params,
            "output_layout_file": str(output_file),
            "num_heliostats": params["num_heliostats"],
            "bubble_radius": params["bubble_radius"],
        }
    )

    firetask.run_task({})

    # Assertions
    assert output_file.exists()
    with open(output_file, newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    assert any(r["param"] == "receiver_height" for r in rows)
    assert any(r["param"] == "north_only" for r in rows)


def test_generate_layout_octagon_spiral(tmp_path, patch_get_layout_generator):
    output_file = tmp_path / "layout_octagon.csv"
    params = {
        "receiver_height": 90.0,
        "receiver_radial_distance": 25.0,
        "receiver_radius": 2.0,
        "octagon_radius": 15.0,
        "receiver_tilt_deg": 10.0,
        "num_heliostats": 1200,
        "bubble_radius": 1.5,
    }

    firetask = GenerateLayoutFromParametersFiretask(
        {
            "generator_type": "octagon_biomimetic_spiral",
            "parameters": params,
            "output_layout_file": str(output_file),
            "num_heliostats": params["num_heliostats"],
            "bubble_radius": params["bubble_radius"],
        }
    )

    firetask.run_task({})

    # Assertions
    assert output_file.exists()
    with open(output_file, newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    assert any(r["param"] == "receiver_radial_distance" for r in rows)
    assert any(r["param"] == "receiver_tilt_deg" for r in rows)