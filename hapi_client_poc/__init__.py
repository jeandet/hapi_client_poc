"""Top-level package for HAPI client POC."""

__author__ = """Jeandet Alexis"""
__email__ = 'alexis.jeandet@member.fsf.org'
__version__ = '0.1.0'

import requests
from urllib.parse import urljoin, urlparse
from typing import Optional, List, Union, Callable, TypeVar, Dict
import json
from functools import partial, singledispatch
import logging
from datetime import datetime, timezone
from dateutil.parser import parse as parse_datetime
import pandas as pds
from contextlib import contextmanager
from . import parsers as hapi_parsers
from . import caching as hapi_caching
from . import multiprocessing as hapi_multiproc

log = logging.getLogger(__name__)


def make_utc_datetime(input_dt: str or datetime) -> datetime:
    if type(input_dt) is str:
        input_dt = parse_datetime(input_dt)
    return input_dt.replace(tzinfo=timezone.utc)


def isoformat(dt: Union[str, datetime]) -> str:
    return make_utc_datetime(dt).isoformat().replace('+00:00', 'Z')


def only_public_members(obj: object) -> Dict:
    return {key: value for key, value in obj.__dict__.items() if not key.startswith('_')}


@singledispatch
def _repr_class(obj, indent=1, level=0) -> str:
    members = only_public_members(obj)
    return (' ' * indent * level) + obj.__class__.__name__ + ':\n' + _repr_class(members, indent, level)


@_repr_class.register(int)
@_repr_class.register(float)
@_repr_class.register(str)
@_repr_class.register(datetime)
@_repr_class.register(type(None))
def _(obj, indent=1, level=0) -> str:
    return str(obj)


@_repr_class.register(dict)
def _(obj, indent=1, level=0) -> str:
    return '\n'.join(
        [(' ' * indent * (level + 1)) + name + ': ' + _repr_class(value, indent=indent, level=level + 1) for
         name, value
         in obj.items()])


@_repr_class.register(list)
@_repr_class.register(tuple)
def _(obj, indent=1, level=0) -> str:
    return '[' + ',\n'.join(
        [(' ' * indent * (level + 1)) + _repr_class(value, indent=indent, level=level + 1) for value in obj]) + ']'


def repr_class(obj: object, indent=1) -> str:
    return _repr_class(obj, indent)


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


_F = TypeVar('_F')


def get_from_endpoint(hapi_url: str, endpoint: str, parameters=None,
                      payload_extractor: Callable[[bytes], _F] = hapi_parsers.json_response) -> Optional[_F]:
    url = build_url(hapi_url, endpoint)
    if parameters is None:
        parameters = {}
    if url:
        log.debug(f"New request url:  {url}?{'&'.join([key + '=' + value for key, value in parameters.items()])}")
        response = requests.get(url, params=parameters)
        if response.ok:
            log.debug(f"success!")
            return payload_extractor(response.content)
    else:
        raise ValueError(f"Given HAPI url seems invalid {hapi_url}")
    return None


class Capabilities:
    def __init__(self, **kwargs):
        self.outputFormats = kwargs.pop('outputFormats')
        self.__dict__.update(kwargs)

    def __repr__(self):
        return json.dumps(self.__dict__, indent=1)


@hapi_caching.CachedRequest
def get_capabilities(hapi_url: str):
    response = get_from_endpoint(hapi_url, Endpoints.CAPABILITIES)
    if response:
        return Capabilities(**response)
    return None


class Parameter:
    def __init__(self, **kwargs):
        self.name = kwargs.pop('name')
        self.type = kwargs.pop('type')
        self.units = kwargs.pop('units')
        self.__dict__.update(kwargs)

    def __repr__(self):
        return repr_class(self)


class DatasetInfo:
    def __init__(self, **kwargs):
        self.startDate = kwargs.pop('startDate')
        self.stopDate = kwargs.pop('stopDate')
        params = kwargs.pop('parameters')
        self.parameters = {param['name']: Parameter(**param) for param in params}
        self.__dict__.update(kwargs)

    def __repr__(self):
        return repr_class(self)


@hapi_caching.CachedRequest
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
    def description(self) -> Optional[DatasetInfo]:
        if self.__description is None:
            self.__description = get_info(self._hapi_url, self.id)
        return self.__description

    def __repr__(self):
        return repr_class(self)


@hapi_caching.CachedRequest
def get_catalog(hapi_url: str) -> Optional[List[Dataset]]:
    response = get_from_endpoint(hapi_url, Endpoints.CATALOG)
    if response:
        return [Dataset(hapi_url, **entry) for entry in response["catalog"]]
    return None


@hapi_multiproc.SplitDataRequest
@hapi_caching.DataRequestCache
def get_data(hapi_url: str, dataset_id: str, start_time: Union[datetime, str],
             stop_time: Union[datetime, str], parameters: Optional[List[str]] = None) -> Optional[pds.DataFrame]:
    desc = get_info(hapi_url=hapi_url, parameter_id=dataset_id)
    request_param = {
        'id': dataset_id,
        'time.min': isoformat(start_time),
        'time.max': isoformat(stop_time),
        'format': 'csv'}
    if parameters is not None and len(parameters):
        if not set(parameters).issubset(desc.parameters.keys()):
            raise ValueError(f"""All parameters must belong to given dataset
Given parameters: {parameters}
Dataset parameters: {desc.parameters.keys()}
""")
        request_param['parameters'] = ','.join(parameters)
    df = get_from_endpoint(hapi_url=hapi_url, endpoint=Endpoints.DATA,
                           parameters=request_param,
                           payload_extractor=hapi_parsers.csv)
    return df


def clear_requests_caches():
    get_catalog.cache_clear()
    get_info.cache_clear()
    get_capabilities.cache_clear()


class Server:
    def __init__(self, hapi_url: str):
        self.__hapi_url = hapi_url
        self.get_capabilities = partial(get_capabilities, hapi_url=hapi_url)
        self.get_catalog = partial(get_catalog, hapi_url=hapi_url)
        self.get_info = partial(get_info, hapi_url)
        self.get_data = partial(get_data, hapi_url)


@contextmanager
def hapi_server(hapi_url: str):
    server = Server(hapi_url)
    try:
        yield server
    finally:
        pass
