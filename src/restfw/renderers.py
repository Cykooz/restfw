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


def build_json_renderer(**kwargs):
    adapters = [
        (datetime.datetime, datetime_adapter),
        (datetime.date, date_adapter),
        (datetime.time, time_adapter),
        (Decimal, decimal_adapter),
    ]
    try:
        from enum import Enum
        adapters.append((Enum, enum_adapter))
    except ImportError:
        pass
    try:
        from bson import ObjectId
        adapters.append((ObjectId, object_id_adapter))
    except ImportError:
        pass

    return JSON(adapters=adapters, **kwargs)


json_renderer = build_json_renderer()
