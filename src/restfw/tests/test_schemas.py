# -*- coding: utf-8 -*-
"""
:Authors: cykooz
:Date: 05.02.2018
"""
import colander
import pytest

from ..schemas import IntegerNode


def test_serialize_empty_integer():
    node = IntegerNode()
    assert node.serialize(0) == '0'
    assert node.serialize(colander.null) is colander.null
    with pytest.raises(colander.Invalid) as ex:
        node.serialize(None)
    assert ex.value.msg == '"${val}" is not a number'
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
