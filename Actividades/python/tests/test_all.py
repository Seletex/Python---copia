import pytest
import actividades_rust


def test_sum_as_string():
    assert actividades_rust.sum_as_string(1, 1) == "2"
