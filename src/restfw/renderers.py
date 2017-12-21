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


def decimal_adapter(obj, request):
    return str(obj)


def object_id_adapter(obj, request):
    return str(obj)


json_renderer = JSON()
json_renderer.add_adapter(datetime.datetime, datetime_adapter)
json_renderer.add_adapter(datetime.date, date_adapter)
json_renderer.add_adapter(Decimal, decimal_adapter)
