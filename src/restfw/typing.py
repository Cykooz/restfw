"""
:Authors: cykooz
:Date: 25.12.2020
"""
from typing import Dict, List, Tuple, Union

from pyramid.registry import Registry
from pyramid.request import Request


JsonNumber = Union[int, float]
SimpleJsonValue = Union[str, JsonNumber, bool, None]
Json = Union[SimpleJsonValue, List['Json'], Tuple['Json', ...], Dict[str, 'Json']]


class PyramidRequest(Request):
    registry: Registry
