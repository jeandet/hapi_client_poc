"""
This has to be implemented.

Many strategies are possible here, could split requests along parameters or time.
A global process pool could be created for each client process.
Maybe this needs to limit concurrent requests on the same server?
"""
from typing import Union, Optional, List
from datetime import datetime
import pandas as pds


class SplitDataRequest:
    def __init__(self, function):
        self.function = function

    def __call__(self, hapi_url: str, dataset_id: str, start_time: Union[datetime, str],
                 stop_time: Union[datetime, str], parameters: Optional[List[str]] = None) -> Optional[pds.DataFrame]:
        return self.function(hapi_url, dataset_id, start_time, stop_time, parameters)
