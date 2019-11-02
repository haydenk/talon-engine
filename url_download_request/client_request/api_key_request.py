"""This module contains the implementation for creating a HTTP Request with Basic Authentication"""
from .url_request import UrlRequest


class ApiKeyRequest(UrlRequest):
    """Basic Authentication Request Implementation"""
    def __init__(self, url: str, **kwargs):
        UrlRequest.__init__(self, url)
        self.location = kwargs.get('location', 'header')
        self.field = kwargs.get('field', '')
        self.value = kwargs.get('value', '')

    def create(self):
        from requests import Request
        req = Request('GET', self.url)

        if self.location.lower() == 'header':
            req.headers.update({self.field: self.value})
        if self.location.lower() == 'query_string':
            req.params.update({self.field: self.value})

        return req.prepare()
