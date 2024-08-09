# -*- coding: utf-8 -*-
"""
:Authors: cykooz
:Date: 05.02.2018
"""

import datetime

import colander
import pendulum
import pytest

from ..hal import SimpleContainer
from ..schemas import (
    DateNode,
    DateTimeNode,
    EmptyStringNode,
    IntegerNode,
    ResourceNode,
    StringNode,
)


def test_serialize_empty_integer():
    node = IntegerNode()
    assert node.serialize(0) == '0'
    assert node.serialize(colander.null) is colander.null
    assert node.serialize(None) is colander.null
    with pytest.raises(colander.Invalid) as ex:
        node.serialize('')
    assert ex.value.msg == '"${val}" is not a number'

    node = IntegerNode(nullable=True)
    assert node.serialize(0) == '0'
    assert node.serialize(colander.null) is colander.null
    assert node.serialize(None) is None
    with pytest.raises(colander.Invalid) as ex:
        node.serialize('')
    assert ex.value.msg == '"${val}" is not a number'


def test_deserialize_empty_integer():
    node = IntegerNode()
    assert node.deserialize('0') == 0
    with pytest.raises(colander.Invalid):
        node.deserialize(None)
    with pytest.raises(colander.Invalid):
        node.deserialize('')
    with pytest.raises(colander.Invalid) as ex:
        node.deserialize(colander.null)
    assert ex.value.msg == 'Required'

    node = IntegerNode(nullable=True)
    assert node.deserialize('0') == 0
    assert node.deserialize(None) is None
    assert node.deserialize('') is None
    with pytest.raises(colander.Invalid) as ex:
        node.deserialize(colander.null)
    assert ex.value.msg == 'Required'


def test_serialize_datetime():
    node = DateTimeNode()
    tz_info = pendulum.timezone('Europe/Moscow')
    now_local = datetime.datetime(2020, 11, 8, 10, 41, 31, 345678)
    now = now_local.replace(tzinfo=tz_info)
    assert node.serialize(now_local) == '2020-11-08T10:41:31.345678'
    assert node.serialize(now) == '2020-11-08T10:41:31.345678+03:00'
    assert node.serialize(colander.null) is colander.null
    assert node.serialize(None) is colander.null
    assert node.serialize('') is colander.null

    node = DateTimeNode(nullable=True)
    assert node.serialize(now_local) == '2020-11-08T10:41:31.345678'
    assert node.serialize(now) == '2020-11-08T10:41:31.345678+03:00'
    assert node.serialize(colander.null) is colander.null
    assert node.serialize(None) is None
    assert node.serialize('') is colander.null

    node = DateTimeNode(default_tzinfo=tz_info)
    assert node.serialize(now_local) == '2020-11-08T10:41:31.345678+03:00'
    assert node.serialize(now) == '2020-11-08T10:41:31.345678+03:00'


def test_deserialize_datetime():
    node = DateTimeNode()
    tz_info = pendulum.timezone('Europe/Moscow')
    now_local = datetime.datetime(2020, 11, 8, 10, 41, 31, 345678)
    now = now_local.replace(tzinfo=tz_info)
    assert node.deserialize(now_local.isoformat()) == now_local
    assert node.deserialize(now.isoformat()) == now
    with pytest.raises(colander.Invalid):
        node.deserialize(None)
    with pytest.raises(colander.Invalid):
        node.deserialize('')
    with pytest.raises(colander.Invalid) as ex:
        node.deserialize(colander.null)
    assert ex.value.msg == 'Required'

    node = DateTimeNode(nullable=True)
    assert node.deserialize(now_local.isoformat()) == now_local
    assert node.deserialize(now.isoformat()) == now
    assert node.deserialize(None) is None
    assert node.deserialize('') is None
    with pytest.raises(colander.Invalid) as ex:
        node.deserialize(colander.null)
    assert ex.value.msg == 'Required'


def test_serialize_empty_date():
    node = DateNode()
    now = pendulum.now()
    assert node.serialize(now.date()) == now.date().isoformat()
    assert node.serialize(colander.null) is colander.null
    assert node.serialize(None) is colander.null
    assert node.serialize('') is colander.null

    node = DateNode(nullable=True)
    assert node.serialize(now.date()) == now.date().isoformat()
    assert node.serialize(colander.null) is colander.null
    assert node.serialize(None) is None
    assert node.serialize('') is colander.null


def test_deserialize_empty_date():
    node = DateNode()
    now = pendulum.now()
    assert node.deserialize(now.date().isoformat()) == now.date()
    with pytest.raises(colander.Invalid):
        node.deserialize(None)
    with pytest.raises(colander.Invalid):
        node.deserialize('')
    with pytest.raises(colander.Invalid) as ex:
        node.deserialize(colander.null)
    assert ex.value.msg == 'Required'

    node = DateNode(nullable=True)
    assert node.deserialize(now.date().isoformat()) == now.date()
    assert node.deserialize(None) is None
    assert node.deserialize('') is None
    with pytest.raises(colander.Invalid) as ex:
        node.deserialize(colander.null)
    assert ex.value.msg == 'Required'


def test_serialize_null_string():
    node = StringNode()
    assert node.serialize('s') == 's'
    assert node.serialize(colander.null) is colander.null
    assert node.serialize(None) == 'None'
    assert node.serialize('') == ''

    node = StringNode(nullable=True)
    assert node.serialize('s') == 's'
    assert node.serialize(colander.null) is colander.null
    assert node.serialize(None) is None
    assert node.serialize('') == ''

    node = EmptyStringNode(nullable=True)
    assert node.serialize('s') == 's'
    assert node.serialize(colander.null) is colander.null
    assert node.serialize(None) is None
    assert node.serialize('') == ''


def test_deserialize_null_string():
    node = StringNode()
    assert node.deserialize('s') == 's'
    with pytest.raises(colander.Invalid):
        node.deserialize(None)
    with pytest.raises(colander.Invalid):
        node.deserialize('')
    with pytest.raises(colander.Invalid) as ex:
        node.deserialize(colander.null)
    assert ex.value.msg == 'Required'

    node = StringNode(nullable=True)
    assert node.deserialize('s') == 's'
    assert node.deserialize(None) is None
    assert node.deserialize('') is None
    with pytest.raises(colander.Invalid) as ex:
        node.deserialize(colander.null)
    assert ex.value.msg == 'Required'

    node = EmptyStringNode(nullable=True)
    assert node.deserialize('s') == 's'
    assert node.deserialize(None) is None
    assert node.deserialize('') == ''
    with pytest.raises(colander.Invalid) as ex:
        node.deserialize(colander.null)
    assert ex.value.msg == 'Required'


def test_resource_node_serialize(pyramid_request):
    resource_node: ResourceNode = ResourceNode().bind(request=pyramid_request)
    root = pyramid_request.root

    container = root['container'] = SimpleContainer()
    assert resource_node.serialize(container) == 'http://localhost/container/'

    not_location_resource = container['not_location'] = 'hello'
    with pytest.raises(colander.Invalid):
        resource_node.serialize(not_location_resource)


def test_resource_node_deserialize(pyramid_request):
    resource_node: ResourceNode = ResourceNode().bind(request=pyramid_request)
    root = pyramid_request.root

    container = root['container'] = SimpleContainer()
    assert resource_node.deserialize('http://localhost/container/') is container

    with pytest.raises(colander.Invalid) as e:
        resource_node.deserialize({'href': 'http://localhost/container/'})
    assert 'is not a string with URL' in e.value.msg

    with pytest.raises(colander.Invalid) as e:
        resource_node.deserialize('//bad_[url')
    assert 'is not a valid URL' in e.value.msg

    with pytest.raises(colander.Invalid) as e:
        resource_node.deserialize('http://localhost/container/not_found')
    assert e.value.msg == 'Resource has not found'
