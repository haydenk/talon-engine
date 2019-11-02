import pytest
from global_threat_level import lambda_function

def test_global_threat_level_has_a_value():
    ret = lambda_function.lambda_handler()
    assert ret == 'green'
