import pytest
from utils.layout_utils import generate_layout_id

def test_generate_layout_id_basic_types():
    params = {
        "a0": 0.25,
        "gamma": 0.01,
        "north_only": True,
        "count": 5,
    }
    layout_id = generate_layout_id("003", params)
    expected = "003_a0_0p25_count_5_gamma_0p01_north_only_true"
    assert layout_id == expected


def test_generate_layout_id_false_bool():
    params = {
        "north_only": False,
    }
    layout_id = generate_layout_id("000", params)
    assert layout_id == "000_north_only_false"


def test_generate_layout_id_string_with_dot():
    params = {
        "strategy": "param.v1",
    }
    layout_id = generate_layout_id("001", params)
    assert layout_id == "001_strategy_parampv1"


def test_generate_layout_id_empty():
    layout_id = generate_layout_id("999", {})
    assert layout_id == "999"


def test_generate_layout_id_key_ordering():
    params = {
        "zeta": 1,
        "alpha": 2,
        "mu": 3,
    }
    layout_id = generate_layout_id("123", params)
    # Sorted keys: alpha, mu, zeta
    assert layout_id == "123_alpha_2_mu_3_zeta_1"