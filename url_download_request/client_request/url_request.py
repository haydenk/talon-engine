"""This module contains the base class for fetching the contents of a URL"""
import abc
from rfc3987 import match


class UrlRequest:
    """Base URL Request Implementation"""
    __metadata__ = abc.ABCMeta

    @abc.abstractmethod
    def create(self):
        """Abstract method definition for creating a request"""
        return

    """This is the base init to accept the URL and validate it for a request."""
    def __init__(self, url: str):
        if match(url, rule='URI') is not None:
            self.url = url
        else:
            raise Exception('Invalid URL: ' + url)
