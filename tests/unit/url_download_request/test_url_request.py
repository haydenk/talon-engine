from client_request.url_request import UrlRequest
from requests import PreparedRequest
import pytest


def test_valid_url():
    req = UrlRequest('https://www.google.com')
    generated_request = req.create()
    assert req.url == 'https://www.google.com'
    assert generated_request is None


@pytest.mark.parametrize("url", ['', 'asdf1234', 'user@email.com'])
def test_invalid_url(url):
    with pytest.raises(Exception):
        UrlRequest(url)


def test_create_anonymous_request():
    expected_url = "https://www.google.com"

    from client_request.anonymous_request import AnonymousRequest
    req = AnonymousRequest(expected_url).create()

    assert req.__class__ is PreparedRequest
    assert expected_url in req.url


def test_create_basic_auth_request():
    expected_url = "https://www.google.com"
    expected_username = "admin"
    expected_password = "admin"
    credentials = ("%s:%s" % (expected_username, expected_password))

    from base64 import b64encode
    expected_encoded_credentials = b64encode(credentials.encode('utf-8'))

    from client_request.basic_auth_request import BasicAuthRequest
    req = BasicAuthRequest(expected_url, username=expected_username, password=expected_password).create()

    assert req.__class__ is PreparedRequest
    assert expected_url in req.url
    assert 'Authorization' in req.headers
    assert req.headers['Authorization'] == 'Basic %s' % expected_encoded_credentials.decode('utf-8')


@pytest.mark.parametrize("expected_location", ['header', 'query_string'])
def test_create_api_key_request(expected_location):
    expected_url = "https://www.google.com"
    expected_api_key_field = "api_key"
    expected_api_key_value = "RnJpIEZlYiAxNSAxNzoyNDoxNyBDU1QgMjAxOQo="

    from client_request.api_key_request import ApiKeyRequest
    req = ApiKeyRequest(
        expected_url,
        location=expected_location,
        field=expected_api_key_field,
        value=expected_api_key_value).create()

    assert req.__class__ is PreparedRequest
    assert expected_url in req.url
    if expected_location == 'header':
        assert expected_api_key_field in req.headers
        assert req.headers[expected_api_key_field] == expected_api_key_value
    if expected_location == 'query_string':
        from urllib.parse import unquote
        parsed_uri = unquote(req.path_url)
        assert expected_api_key_field in parsed_uri
        assert expected_api_key_value in parsed_uri
