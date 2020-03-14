# -*- coding: utf-8 -*-
"""
:Authors: cykooz
:Date: 05.03.2020
"""
from pyramid.httpexceptions import HTTPNotFound

from restfw.config import sub_resource_config
from restfw.hal import HalResource, HalResourceWithEmbedded, iter_to_embedded_resources
from restfw.interfaces import MethodOptions
from storage.users.resources import User
from . import schemas
from .models import FileModel


class File(HalResource):
    url_placeholder = '<file_name>'

    def __init__(self, model, parent):
        """
        :type model: FileModel
        :type parent: Files
        """
        self.model = model
        self.__parent__ = parent
        self.__name__ = model.name

    options_for_get = MethodOptions(None, schemas.FileSchema, permission='files.get')

    def as_dict(self, request):
        return {
            'name': self.__name__,
            'size': self.model.size,
        }

    def http_get(self, request, params):
        if not self.model.exists:
            raise HTTPNotFound()
        return super(File, self).http_get(request, params)

    options_for_put = MethodOptions(None, schemas.FileSchema, permission='files.edit')

    def http_put(self, request, params):
        """
        :type request: pyramid.request.Request
        :type params: dict
        """
        self.model.write(request.body)
        created = True
        return self, created

    options_for_delete = MethodOptions(None, None, permission='files.edit')

    def http_delete(self, request, params):
        self.model.delete()


@sub_resource_config('files', User)
class Files(HalResourceWithEmbedded):

    def __init__(self, parent):
        """
        :type parent: User
        """
        self.user = parent
        self.dir_path = parent.model.path

    def __getitem__(self, item):
        if item in ('.', '..'):
            raise KeyError(item)
        model = FileModel(self.dir_path / item)
        return File(model, parent=self)

    options_for_get = MethodOptions(schemas.GetFilesSchema, schemas.FilesSchema,
                                    permission='files.get')

    def get_embedded(self, request, params):
        paths = (path for path in self.dir_path.iterdir() if path.is_file())
        files = (File(FileModel(path), parent=self) for path in paths)
        return iter_to_embedded_resources(
            request, params, files,
            parent=self,
            embedded_name='files',
        )
