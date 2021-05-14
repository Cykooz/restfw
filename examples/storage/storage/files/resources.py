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

    def __init__(self, model: FileModel, parent: 'Files'):
        self.model = model
        self.__parent__ = parent
        self.__name__ = model.name

    def http_put(self, request, params):
        self.model.write(request.body)
        created = True
        return created

    def http_delete(self, request, params):
        self.model.delete()


@sub_resource_config('files')
class Files(HalResource):

    def __init__(self, parent: User):
        self.__parent__ = parent
        self.user = parent
        self.dir_path = parent.model.path

    def __getitem__(self, item):
        if item in ('.', '..'):
            raise KeyError(item)
        model = FileModel(self.dir_path / item)
        return File(model, parent=self)
