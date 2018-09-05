# -*- coding: utf-8 -*-
"""
:Authors: cykooz
:Date: 21.02.2016
"""
import datetime
from decimal import Decimal

from pyramid.renderers import JSON


def datetime_adapter(obj, request):
    return obj.isoformat()


def date_adapter(obj, request):
    return obj.strftime('%Y-%m-%d')


def time_adapter(obj, request):
    return obj.strftime('%H:%M:%S')


def decimal_adapter(obj, request):
    return str(obj)


def object_id_adapter(obj, request):
    return str(obj)


def enum_adapter(obj, request):
    """For Python 3 enums"""
    return obj.name


json_renderer = JSON()
json_renderer.add_adapter(datetime.datetime, datetime_adapter)
json_renderer.add_adapter(datetime.date, date_adapter)
json_renderer.add_adapter(datetime.time, time_adapter)
json_renderer.add_adapter(Decimal, decimal_adapter)


try:
    from enum import Enum
    json_renderer.add_adapter(Enum, enum_adapter)
except ImportError:
    pass
