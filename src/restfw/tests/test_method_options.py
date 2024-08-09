# -*- coding: utf-8 -*-
"""
:Authors: cykooz
:Date: 28.02.2019
"""

import colander

from ..interfaces import MethodOptions


class Schema1(colander.MappingSchema):
    pass


class Schema2(colander.MappingSchema):
    pass


class Schema3(colander.MappingSchema):
    pass


def test_replace():
    options = MethodOptions(Schema1, Schema2)

    new_options = options.replace()
    assert new_options is not options
    assert new_options.input_schema is Schema1
    assert new_options.output_schema is Schema2
    assert new_options.permission is None

    new_options = options.replace(permission='resource.get')
    assert new_options.input_schema is Schema1
    assert new_options.output_schema is Schema2
    assert new_options.permission == 'resource.get'

    new_options = options.replace(
        input_schema=Schema3, permission='resource.edit', unknown_field=1
    )
    assert new_options.input_schema is Schema3
    assert new_options.output_schema is Schema2
    assert new_options.permission == 'resource.edit'
    assert not hasattr(new_options, 'unknown_field')
