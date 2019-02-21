# -*- coding: utf-8 -*-
"""
:Authors: cykooz
:Date: 05.02.2018
"""
import colander
import datetime
import pytest
import pytz

from ..schemas import IntegerNode, DateTimeNode, DateNode


def test_serialize_empty_integer():
    node = IntegerNode()
    assert node.serialize(0) == '0'
    assert node.serialize(colander.null) is colander.null
    assert node.serialize(None) is colander.null
    with pytest.raises(colander.Invalid) as ex:
        node.serialize('')
    assert ex.value.msg == '"${val}" is not a number'

    node = IntegerNode(allow_empty=True)
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

    node = IntegerNode(allow_empty=True)
    assert node.deserialize('0') == 0
    assert node.deserialize(None) is None
    assert node.deserialize('') is None
    with pytest.raises(colander.Invalid) as ex:
        node.deserialize(colander.null)
    assert ex.value.msg == 'Required'


def test_serialize_empty_datetime():
    node = DateTimeNode()
    now = datetime.datetime.utcnow().replace(tzinfo=pytz.UTC)
    assert node.serialize(now) == now.isoformat()
    assert node.serialize(colander.null) is colander.null
    assert node.serialize(None) is colander.null
    assert node.serialize('') is colander.null

    node = DateTimeNode(allow_empty=True)
    assert node.serialize(now) == now.isoformat()
    assert node.serialize(colander.null) is colander.null
    assert node.serialize(None) is None
    assert node.serialize('') is colander.null


def test_deserialize_empty_datetime():
    node = DateTimeNode()
    now = datetime.datetime.utcnow().replace(tzinfo=pytz.UTC)
    assert node.deserialize(now.isoformat()) == now
    with pytest.raises(colander.Invalid):
        node.deserialize(None)
    with pytest.raises(colander.Invalid):
        node.deserialize('')
    with pytest.raises(colander.Invalid) as ex:
        node.deserialize(colander.null)
    assert ex.value.msg == 'Required'

    node = DateTimeNode(allow_empty=True)
    assert node.deserialize(now.isoformat()) == now
    assert node.deserialize(None) is None
    assert node.deserialize('') is None
    with pytest.raises(colander.Invalid) as ex:
        node.deserialize(colander.null)
    assert ex.value.msg == 'Required'


def test_serialize_empty_date():
    node = DateNode()
    now = datetime.datetime.utcnow().replace(tzinfo=pytz.UTC)
    assert node.serialize(now.date()) == now.date().isoformat()
    assert node.serialize(colander.null) is colander.null
    assert node.serialize(None) is colander.null
    assert node.serialize('') is colander.null

    node = DateNode(allow_empty=True)
    assert node.serialize(now.date()) == now.date().isoformat()
    assert node.serialize(colander.null) is colander.null
    assert node.serialize(None) is None
    assert node.serialize('') is colander.null


def test_deserialize_empty_date():
    node = DateNode()
    now = datetime.datetime.utcnow().replace(tzinfo=pytz.UTC)
    assert node.deserialize(now.date().isoformat()) == now.date()
    with pytest.raises(colander.Invalid):
        node.deserialize(None)
    with pytest.raises(colander.Invalid):
        node.deserialize('')
    with pytest.raises(colander.Invalid) as ex:
        node.deserialize(colander.null)
    assert ex.value.msg == 'Required'

    node = DateNode(allow_empty=True)
    assert node.deserialize(now.date().isoformat()) == now.date()
    assert node.deserialize(None) is None
    assert node.deserialize('') is None
    with pytest.raises(colander.Invalid) as ex:
        node.deserialize(colander.null)
    assert ex.value.msg == 'Required'
