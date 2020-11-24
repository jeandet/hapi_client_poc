from typing import Optional, Dict
import json
from io import BytesIO
import pandas as pds


def is_ok(response: Dict):
    return response['status']["message"] == "OK" and response['status']['code'] == 1200


def json_response(data: bytes) -> Optional[Dict]:
    data = json.load(BytesIO(data))
    if is_ok(data):
        data.pop('status')
        data.pop('HAPI')
        return data
    return None


def csv(data: bytes) -> Optional[pds.DataFrame]:
    if len(data):
        df = pds.read_csv(BytesIO(data), index_col=0, parse_dates=True, header=None)
        return df
    return None
