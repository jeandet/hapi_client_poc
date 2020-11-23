"""Top-level package for HAPI client POC."""

__author__ = """Jeandet Alexis"""
__email__ = 'alexis.jeandet@member.fsf.org'
__version__ = '0.1.0'

import requests
from functools import lru_cache
from urllib.parse import urljoin, urlparse
from typing import Optional, Dict, List
import logging

log = logging.getLogger(__name__)


class __CachedRequest:
    def __init__(self, function):
        self.cache = {}
        self.function = function

    def __call__(self, *args, **kwargs):
        key = (args, frozenset(kwargs.items()))
        if key in self.cache:
            return self.cache[key]
        else:
            result = self.function(*args, **kwargs)
            if result is not None:
                self.cache[key] = result
            return result

    def cache_clear(self):
        self.cache.clear()


class Endpoints:
    CATALOG = 'catalog'
    CAPABILITIES = 'capabilities'
    INFO = 'info'
    DATA = 'data'


def build_url(url: str, part: str) -> Optional[str]:
    url = urlparse(urljoin(url + '/', part))
    if all([url.scheme, url.hostname]):
        return url.geturl()
    else:
        return None


def parse_status(response: Dict) -> Optional[Dict]:
    if response['status']["message"] == "OK" and response['status']['code'] == 1200:
        response.pop('status')
        response.pop('HAPI')
        return response
    return None


def get_from_endpoint(hapi_url: str, endpoint: str, parameters=None) -> Optional[Dict]:
    url = build_url(hapi_url, endpoint)
    if url:
        log.debug(f"New request url:{hapi_url}, endpoint: {endpoint}, parameters:{parameters}")
        response = requests.get(url, params=parameters)
        if response.ok:
            log.debug(f"success!")
            response = parse_status(response.json())
            if response:
                return response
    else:
        raise ValueError(f"Given HAPI url seems invalid {hapi_url}")
    return None


class Capabilities:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

    def __repr__(self):
        return f'''outputFormats: {self.outputFormats}'''


@__CachedRequest
def get_capabilities(hapi_url: str):
    response = get_from_endpoint(hapi_url, Endpoints.CAPABILITIES)
    if response:
        return Capabilities(**response)
    return None


class Parameter:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

    def __repr__(self):
        return f'''Parameter: {self.__dict__}'''


class DatasetInfo:
    def __init__(self, **kwargs):
        params = kwargs.pop('parameters')
        self.parameters = [Parameter(**param) for param in params]
        self.__dict__.update(kwargs)

    def __repr__(self):
        return f'''Dataset Description: {self.__dict__}'''


@__CachedRequest
def get_info(hapi_url: str, parameter_id: str) -> Optional[DatasetInfo]:
    response = get_from_endpoint(hapi_url, Endpoints.INFO, {'id': parameter_id})
    if response:
        return DatasetInfo(**response)
    return None


class Dataset:

    def __init__(self, hapi_url, **kwargs):
        self.id = kwargs.pop('id')  # just to get completion from IDE
        self.title = kwargs.pop('title')
        self.__dict__.update(kwargs)
        self.__description = None
        self._hapi_url = hapi_url

    @property
    def description(self):
        if self.__description is None:
            self.__description = get_info(self._hapi_url, self.id)
        return self.__description

    def __repr__(self):
        return f'''Dataset: id {self.id}, title {self.title}'''


@__CachedRequest
def get_catalog(hapi_url: str) -> Optional[List[Dataset]]:
    response = get_from_endpoint(hapi_url, Endpoints.CATALOG)
    if response:
        return [Dataset(hapi_url, **entry) for entry in response["catalog"]]
    return None


def clear_requests_caches():
    get_catalog.cache_clear()
    get_info.cache_clear()
    get_capabilities.cache_clear()
