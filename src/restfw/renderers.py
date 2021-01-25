# -*- coding: utf-8 -*-
"""
:Authors: cykooz
:Date: 21.02.2016
"""
import datetime
from decimal import Decimal

from pyramid.renderers import JSON

from .interfaces import IResource
from .typing import PyramidRequest
from .views import get_resource_view


def resource_adapter(obj: IResource, request: PyramidRequest):
    view = get_resource_view(obj, request)
    if view:
        return view.__json__()
    return {}


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
        (IResource, resource_adapter),
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


json_renderer = build_json_renderer(ensure_ascii=False)


def add_adapter_into_json_renderer(type_or_iface, adapter):
    json_renderer.add_adapter(type_or_iface, adapter)


JSON_RENDER = json_renderer(None)
