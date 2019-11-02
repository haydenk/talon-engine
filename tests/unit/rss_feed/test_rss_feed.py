import pytest
from rss_feed import lambda_function

def test_rss_returns_value():
	val = lambda_function.lambda_handler()
	assert len(val) != 0 , "We have a list"
