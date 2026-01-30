"""
:Authors: cykooz
:Date: 12.01.2021
"""

from zope.interface.verify import verifyObject

from .common import derive_fabric
from .. import interfaces


def add_external_link_fabric(
    config,
    fabric,
    name,
    resource_type=interfaces.IHalResource,
    title='',
    description='',
    optional=False,
    templated=False,
    **predicates,
):
    """A configurator command for register a fabric of external link.
    :type config: pyramid.config.Configurator
    :type fabric: interfaces.IExternalLinkFabric
    :type name: str
    :type resource_type: type or zope.interface.Interface
    :type title: str
    :type description: str
    :type optional: bool
    :type templated: bool
    :type predicates: dict

    Using the default ``resource_type`` value, ``IHalResource`` will cause the fabric
    of external link to be registered for all HAL-resource types.

    Any number of predicate keyword arguments may be passed in
    ``**predicates``. Each predicate named will narrow the set of
    circumstances in which the fabric of external link will be invoked.
    Each named predicate must have been registered via
    :meth:`restfw.config.add_external_link_fabric_predicate` before it
    can be used.
    """

    dotted = config.maybe_dotted
    fabric, resource_type = dotted(fabric), dotted(resource_type)
    verifyObject(interfaces.IExternalLinkFabric, fabric, tentative=True)

    if not isinstance(resource_type, (tuple, list)):
        resource_type = (resource_type,)

    intr = config.introspectable(
        category_name='External link fabrics',
        discriminator=id(fabric),
        title=config.object_description(fabric),
        type_name='external link fabric',
    )
    intr['fabric'] = fabric
    intr['resource_type'] = resource_type
    _title = title
    _description = description
    _optional = optional
    _templated = templated

    class ExternalLinkFabric:
        title = _title
        description = _description
        optional = _optional
        templated = _templated

        def __init__(self, resource):
            self._resource = resource

        def get_link(self, request):
            return fabric(request, self._resource)

    def register():
        pred_list = config.get_predlist('external_link_fabric')
        order, preds, phash = pred_list.make(config, **predicates)

        derived_fabric = derive_fabric(ExternalLinkFabric, preds)

        intr.update(
            {
                'phash': phash,
                'order': order,
                'predicates': preds,
                'derived_fabric': derived_fabric,
            }
        )

        config.registry.registerAdapter(
            derived_fabric,
            required=resource_type,
            provided=interfaces.IExternalLinkAdapter,
            name=name,
        )

    config.action(None, register, introspectables=(intr,))
    return fabric


def add_external_link_fabric_predicate(
    config,
    name,
    factory,
    weighs_more_than=None,
    weighs_less_than=None,
):
    """
    :type config: pyramid.config.Configurator
    :type name: str
    :param factory:
    :param weighs_more_than:
    :param weighs_less_than:

    Adds a predicate factory for fabrics of external link. The associated
    predicate can later be named as a keyword argument to
    :meth:`pyramid.config.Configurator.add_external_link_fabric` in the
    ``**predicates`` anonymous keyword argument dictionary.

    ``name`` should be the name of the predicate.  It must be a valid
    Python identifier (it will be used as a ``**predicates`` keyword
    argument to :meth:`~restfw.config.add_external_link_fabric`).

    ``factory`` should be a :term:`predicate factory` or :term:`dotted
    Python name` which refers to a predicate factory.
    """
    config._add_predicate(
        'external_link_fabric',
        name,
        factory,
        weighs_more_than=weighs_more_than,
        weighs_less_than=weighs_less_than,
    )
