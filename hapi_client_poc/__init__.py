"""Top-level package for HAPI client POC."""

__author__ = """Jeandet Alexis"""
__email__ = 'alexis.jeandet@member.fsf.org'
__version__ = '0.1.0'

import requests
from urllib.parse import urljoin, urlparse
from typing import Optional, Dict, List
import logging

log = logging.getLogger(__name__)


class Endpoints:
    CATALOG = 'catalog'
    CAPABILITIES = 'capabilities'
    INFO = 'info'


def build_url(url: str, part: str) -> Optional[str]:
    url = urlparse(urljoin(url, part))
    if all([url.scheme, url.hostname]):
        return url.geturl()
    else:
        return None


def get_from_endpoint(hapi_url: str, endpoint: str, parameters=None) -> Optional[Dict]:
    url = build_url(hapi_url, endpoint)
    if url:
        log.debug(f"New request url:{hapi_url}, endpoint: {endpoint}, parameters:{parameters}")
        response = requests.get(url, params=parameters)
        if response.ok:
            log.debug(f"success!")
            response = response.json()
            if response['status']["message"] == "OK":
                response.pop('status')
                response.pop('HAPI')
                return response
    else:
        raise ValueError(f"Given HAPI url seems invalid {hapi_url}")
    return None


class Parameter:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


class DatasetInfo:
    def __init__(self, **kwargs):
        params = kwargs.pop('parameters')
        self.parameters = [Parameter(**param) for param in params]
        self.__dict__.update(kwargs)


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
        self._description = None
        self._hapi_url = hapi_url

    @property
    def description(self):
        if self._description is None:
            self._description = get_info(self._hapi_url, self.id)
        return self._description

    def __repr__(self):
        return f'''Dataset: id {self.id}, title {self.title}'''


def get_catalog(hapi_url: str) -> Optional[List[Dataset]]:
    response = get_from_endpoint(hapi_url, Endpoints.CATALOG)
    if response:
        return [Dataset(hapi_url, **entry) for entry in response["catalog"]]
    return None
