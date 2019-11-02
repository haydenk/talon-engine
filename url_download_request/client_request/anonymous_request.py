"""This module contains the implementation for creating an Anonymous HTTP Request"""
from .url_request import UrlRequest


class AnonymousRequest(UrlRequest):
    """Anonymous Request Implementation"""
    def create(self):
        from requests import Request
        req = Request('GET', self.url)
        return req.prepare()
