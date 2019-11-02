"""This module contains the implementation for creating a HTTP Request with Basic Authentication"""
from .url_request import UrlRequest


class BasicAuthRequest(UrlRequest):
    """Basic Authentication Request Implementation"""
    def __init__(self, url: str, **kwargs):
        UrlRequest.__init__(self, url)
        self.username = kwargs.get('username')
        self.password = kwargs.get('password')

    def create(self):
        from requests import Request
        req = Request('GET', self.url, auth=(self.username, self.password))
        return req.prepare()
