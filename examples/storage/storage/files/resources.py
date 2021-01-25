"""
:Authors: cykooz
:Date: 05.03.2020
"""
from restfw.hal import HalResource
from restfw.resources import sub_resource_config
from .models import FileModel
from ..users.resources import User


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

    def http_put(self, request, params):
        """
        :type request: pyramid.request.Request
        :type params: dict
        """
        self.model.write(request.body)
        created = True
        return created

    def http_delete(self, request, params):
        self.model.delete()


@sub_resource_config('files', User)
class Files(HalResource):

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
