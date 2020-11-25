from typing import Union, Optional, List
from datetime import datetime
import pandas as pds


class CachedRequest:
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


"""
has to be implemented, a simple, safe and efficient solution would be to use diskcache with the following impl:
One entry per parameter per constant time slice (12h? or computed from sampling rate to use an optimum cache entry size)
Cache entry keys would be f'{server_url}/{dataset_id}/{parameter_name}/{start_time.isoformat()}'
This gives realy good performances on spwc.
"""


class DataRequestCache:
    def __init__(self, function):
        self.function = function

    def __call__(self, hapi_url: str, dataset_id: str, start_time: Union[datetime, str],
                 stop_time: Union[datetime, str], parameters: Optional[List[str]] = None) -> Optional[pds.DataFrame]:
        return self.function(hapi_url, dataset_id, start_time, stop_time, parameters)
