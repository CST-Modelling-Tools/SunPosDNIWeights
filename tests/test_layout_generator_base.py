# tests/test_layout_generator_base.py

import pytest
from layout_generators.layout_generator_base import ParametricLayoutGenerator
from pathlib import Path
from abc import ABCMeta

def test_base_class_is_abstract():
    assert isinstance(ParametricLayoutGenerator, ABCMeta), "Base class must be abstract"

def test_generate_layout_is_abstract():
    with pytest.raises(TypeError):
        class BadGenerator(ParametricLayoutGenerator):
            pass

        # This should raise a TypeError due to unimplemented abstract method
        BadGenerator()