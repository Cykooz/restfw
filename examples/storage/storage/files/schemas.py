# -*- coding: utf-8 -*-
"""
:Authors: cykooz
:Date: 05.03.2020
"""
import colander

from restfw import schemas


class FileSchema(schemas.HalResourceSchema):
    name = schemas.StringNode(title='Name')
    size = schemas.UnsignedIntegerNode(title='File size')


class GetFilesSchema(schemas.GetEmbeddedSchema):
    pass


class FilesSchema(schemas.HalResourceWithEmbeddedSchema):
    _embedded = schemas.EmbeddedNode(
        colander.SequenceSchema(
            FileSchema(title='File'),
            name='files',
            title='List of embedded files'
        ),
        missing=colander.drop
    )
