"""Top-level package for HAPI client POC."""

__author__ = """Jeandet Alexis"""
__email__ = 'alexis.jeandet@member.fsf.org'
__version__ = '0.1.0'

import requests
from urllib.parse import urljoin, urlparse
from typing import Optional, Dict, List


class Dataset:
    __slots__ = ['id', 'title']

    def __init__(self, id, title=None):
        self.id = id
        self.title = title


def build_url(url: str, part: str) -> Optional[str]:
    url = urlparse(urljoin(url, part))
    if all([url.scheme, url.hostname]):
        return url.geturl()
    else:
        return None


def get_from_endpoint(hapi_url: str, endpoint: str) -> Optional[Dict]:
    url = build_url(hapi_url, endpoint)
    if url:
        response = requests.get(urljoin(hapi_url, 'catalog'))
        if response.ok:
            response = response.json()
            if response['status']["message"] == "OK":
                return response
    else:
        raise ValueError(f"Given HAPI url seems invalid {hapi_url}")


def get_catalog(hapi_url: str) -> Optional[List[Dataset]]:
    response = get_from_endpoint(hapi_url, 'catalog')
    if response:
        return [Dataset(**entry) for entry in response["catalog"]]
    return None
