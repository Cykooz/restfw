# -*- coding: utf-8 -*-
"""
:Authors: cykooz
:Date: 10.07.2019
"""
import colander
import pytest

from .. import schemas
from ..utils import create_validation_error


class ObjSchema(schemas.MappingNode):
    cost = schemas.FloatNode()


class SubSchema(schemas.MappingNode):
    value = schemas.UnsignedIntegerNode()
    int_list = schemas.SequenceNode(schemas.UnsignedIntegerNode())
    obj_list = schemas.SequenceNode(ObjSchema())


class SomeSchema(schemas.MappingNode):
    name = schemas.StringNode(title='Name')
    sub = SubSchema()


def test_create_validation_error():
    params = {
        'name': '',
        'sub': {
            'value': -1,
            'int_list': [1, 2, -1, 3, 'abc'],
            'obj_list': [
                {'cost': 0},
                {'cost': 1.2},
                {'cost': 'abcd'},
                {},
                'abcd',
            ]
        }
    }
    schema = SomeSchema()

    with pytest.raises(colander.Invalid) as exc_info:
        schema.deserialize(params)

    exc = exc_info.value  # type: colander.Invalid
    detail = exc.asdict()
    assert detail == {
        'name': 'Required',
        'sub.value': '-1 is less than minimum value 0',
        'sub.int_list.2': '-1 is less than minimum value 0',
        'sub.int_list.4': '"abc" is not a number',
        'sub.obj_list.2.cost': '"abcd" is not a number',
        'sub.obj_list.3.cost': 'Required',
        'sub.obj_list.4': '"abcd" is not a mapping type: Does not implement dict-like functionality.',
    }

    err_msg = 'Error message'

    err = create_validation_error(SomeSchema, err_msg)
    assert err.detail == {
        '': err_msg,
    }

    for node_name in ['name', 'sub', 'sub.value', 'sub.int_list', 'sub.int_list.2',
                      'sub.obj_list', 'sub.obj_list.2', 'sub.obj_list.2.cost']:
        err = create_validation_error(SomeSchema, err_msg, node_name)
        assert err.detail == {
            node_name: err_msg,
        }
