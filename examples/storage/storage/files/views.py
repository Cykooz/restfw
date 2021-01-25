"""
:Authors: cykooz
:Date: 13.01.2021
"""
from pyramid.httpexceptions import HTTPNotFound

from restfw import views
from restfw.interfaces import MethodOptions
from restfw.views import iter_to_embedded_resources
from . import schemas
from .models import FileModel
from .resources import File, Files


@views.resource_view_config()
class FileView(views.HalResourceView):
    resource: File
    options_for_get = MethodOptions(None, schemas.FileSchema, permission='files.get')
    options_for_put = MethodOptions(None, schemas.FileSchema, permission='files.edit')
    options_for_delete = MethodOptions(None, None, permission='files.edit')

    def as_dict(self):
        return {
            'name': self.resource.__name__,
            'size': self.resource.model.size,
        }

    def http_get(self):
        if not self.resource.model.exists:
            raise HTTPNotFound()
        return super().http_get()


@views.resource_view_config()
class FilesView(views.HalResourceWithEmbeddedView):
    resource: Files
    options_for_get = MethodOptions(schemas.GetFilesSchema, schemas.FilesSchema,
                                    permission='files.get')

    def get_embedded(self, params):
        paths = (
            path
            for path in self.resource.dir_path.iterdir()
            if path.is_file()
        )
        files = (
            File(FileModel(path), parent=self.resource)
            for path in paths
        )
        return iter_to_embedded_resources(
            self.request, params, files,
            parent=self.resource,
            embedded_name='files',
        )
