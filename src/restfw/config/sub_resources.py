"""
:Authors: cykooz
:Date: 12.01.2021
"""

from pyramid.config import Configurator
from zope.interface.verify import verifyObject

from .common import derive_fabric
from .. import interfaces


def add_sub_resource_fabric(
    config: Configurator,
    fabric,
    name: str,
    parent=interfaces.IResource,
    add_link_into_embedded=False,
    **predicates,
):
    """A configurator command for register sub-resource fabric.
    :param fabric: Object that provides interfaces.ISubResourceFabric
    :param parent: type or zope.interface.Interface

    Using the default ``parent`` value, ``IResource`` will cause the sub resource
    fabric to be registered for all resource types.

    Any number of predicate keyword arguments may be passed in
    ``**predicates``.  Each predicate named will narrow the set of
    circumstances in which the sub resource fabric will be invoked. Each named
    predicate must have been registered via
    :meth:`restfw.config.add_sub_resource_fabric_predicate` before it
    can be used.
    """

    dotted = config.maybe_dotted
    fabric, parent = dotted(fabric), dotted(parent)
    verifyObject(interfaces.ISubResourceFabric, fabric, tentative=True)

    if not isinstance(parent, (tuple, list)):
        parent = (parent,)

    intr = config.introspectable(
        category_name='Sub-resource fabrics',
        discriminator=id(fabric),
        title=config.object_description(fabric),
        type_name='sub-resource fabric',
    )
    intr['fabric'] = fabric
    intr['parent'] = parent
    intr['add_link_into_embedded'] = add_link_into_embedded

    def register():
        pred_list = config.get_predlist('sub_resource_fabric')
        order, preds, phash = pred_list.make(config, **predicates)
        derived_fabric = derive_fabric(fabric, preds)

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
            required=parent,
            provided=interfaces.IResource,
            name=name,
        )
        if add_link_into_embedded:
            add_into_embedded_fabric = derive_fabric(_add_into_embedded_fabric, preds)
            config.registry.registerAdapter(
                add_into_embedded_fabric,
                required=parent,
                provided=interfaces.IAddSubresourceLinkIntoEmbedded,
                name=name,
            )

    config.action(None, register, introspectables=(intr,))
    return fabric


def _add_into_embedded_fabric(resource):
    return True


def add_sub_resource_fabric_predicate(
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

    Adds a sub resource fabric predicate factory. The associated
    sub resource fabric predicate can later be named as a keyword argument to
    :meth:`pyramid.config.Configurator.add_sub_resource_fabric` in the
    ``**predicates`` anonymous keyword argument dictionary.

    ``name`` should be the name of the predicate.  It must be a valid
    Python identifier (it will be used as a ``**predicates`` keyword
    argument to :meth:`~restfw.config.add_sub_resource_fabric`).

    ``factory`` should be a :term:`predicate factory` or :term:`dotted
    Python name` which refers to a predicate factory.
    """
    config._add_predicate(
        'sub_resource_fabric',
        name,
        factory,
        weighs_more_than=weighs_more_than,
        weighs_less_than=weighs_less_than,
    )
