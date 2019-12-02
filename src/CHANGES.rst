..  Changelog format guide.
    - Before make new release of core egg you MUST add here a header for new version with name "Next release".
    - After all headers and paragraphs you MUST add only ONE empty line.
    - At the end of sentence which describes some changes SHOULD be identifier of task from our task manager.
      This identifier MUST be placed in brackets. If a hot fix has not the task identifier then you
      can use the word "HOTFIX" instead of it.
    - At the end of sentence MUST stand a point.
    - List of changes in the one version MUST be grouped in the next sections:
        - Features
        - Changes
        - Bug Fixes
        - Docs

CHANGELOG
*********

3.4b1 (2019-12-02)
==================

Features
--------

- Added argument ``description`` for function ``send()`` used inside of ``Usage Examples``.
- Documentation generator include only first example request from all of with equal
  ``status code`` and not empty ``description``.

Bug Fixes
---------

- Added encoding of class name in function ``clone_schema_class`` for Python 2.

3.3.2 (2019-11-08)
==================

Bug Fixes
---------

- Fixed checking of ``Location`` header in ``assert_resource()`` function.

3.3 (2019-11-08)
================

Features
--------

- Added new schema ``PreserveMappingSchema``.

Changes
-------

- Updated dependencies.

Bug Fixes
---------

- Now ``Location`` header do not adds into response if has created
  resource do not provide ``ILocation``.

3.2 (2019-08-30)
================

Changes
-------

- Improved generation application name inside of ``RstDocGenerator``.
- Improved JSON serializer for ``colander_2_json_schema``.

3.1 (2019-07-23)
================

Features
--------

- Added support Python 2 into ``WebApp``.

Changes
-------

- Fixed error detail for ``HTTPNotFound`` exception.

3.0.4 (2019-07-10)
==================

Bug Fixes
---------

- Added support of complex values of ``node_name`` argument of
  ``create_validation_error()`` function. For example:

  .. code-block:: python

    create_validation_error(
        SchemaClass, 'Error message',
        node_name='sub.obj_list.2.cost'
    )

3.0.2 (2019-04-11)
==================

Changes
-------

- Changed order of sending ``GET`` and ``HEAD`` requests in ``GetRequestsTester``.

3.0 (2019-04-03)
================

Features
--------

- Added new Nullable type to allow empty value for any schema type.
  Added support of empty values for ``DateTimeNode`` and ``DateNode``.
- Added new colander type ``ResourceType`` - a type representing
  a resource object that supports ``ILocation`` interface.
- Added new colander node ``ResourceNode``.
- Added new colander validator ``ResourceInterface`` - a validator which
  succeeds if the type or interface of value passed to it is one of
  a fixed set of interfaces and classes.
- Improved tools to create resource usage examples:

    - ``restfw.resources_info.ResourceInfo`` moved to
      ``restfw.usage_examples.UsageExamples``;
    - added configurator directives ``add_usage_examples_fabric`` and
      ``add_usage_examples_fabric_predicate``;
    - added decorator ``restfw.usage_examples.examples_config`` to
      declarative registration of usage examples fabric;
    - added utility ``restfw.usage_examples.collector.UsageExamplesCollector``
      what collects full information about all registered resource usage
      examples.

- Added utility ``restfw.docs_gen.rst_doc_generator.RstDocGenerator`` that
  generates rst-files (reStructuredText) with documentation based on
  information collected from usage examples.
- Added view for exception ``HTTPForbidden``.
- Added method ``replace`` into ``MethodOptions`` class.
- Added field ``resource`` into detail about ``HTTP 404`` error with path
  to resource what has not found.

Bug Fixes
---------

- Response with 304 status code do not change in ``http_exception_view`` now.
- ``WebApp.url_prefix`` do not use now to choose method of sending file in tests.
- Fixed error with using ``list`` value for argument ``params`` of ``send``
  function inside of UsageExamples methods.

Backward Incompatible Changes
-----------------------------

- Deleted class ``restfw.resources_info.ResourceInfo``.
- Delete from main dependencies package ``pyramid_jinja2``.
- Deleted schema type ``restfw.schemas.Integer``.
- Deleted function ``restfw.utils.register_resource_info``
- Deleted all deprecated code:

    - ``restfw.testing.get_pyramid_root``
    - ``restfw.testing.open_pyramid_request``
    - ``restfw.testing.webapp.WebApp.request``
    - ``restfw.testing.webapp.WebApp.root``
    - ``restfw.resources.sub_resource_config``

2.2.2 (2018-12-10)
==================

Changes
-------

- Added argument ``headers`` into method ``WebApp.download_file()``.

2.2 (2018-11-23)
================

Features
--------

- Added support of predicates to sub resource fabrics.
- Added ``Configurator`` directive ``add_sub_resource_fabric_predicate`` to
  register predicates for sub resource fabrics.

Backward Incompatible Changes
-----------------------------

- Sub resources creates now also during build of links to them form parent resource.
  Before this release sub resources did not create - building of links used only
  name of sub resources.
- Fabrics of sub resources must not raise ``KeyError`` exception. Instead of it
  they must returns ``None``.

2.1.10 (2018-09-18)
===================

Bug Fixes
---------

- Fixed ``Resource.__getitem__()`` - key now converts to string.

2.1.8 (2018-09-05)
==================

Bug Fixes
---------

- Fixed small error in ``WebApp.download_file``.

2.1.2 (2018-09-05)
==================

Changes
-------

- Added some type hinting.

2.1 (2018-08-31)
================

Features
--------

- Added offset+limit case to function ``assert_container_listing``.
- Added fix for memory leaks on pyramid segment cache.

Changes
-------

- ``WebApp.request`` and ``WebApp.root`` has marked as deprecated.

Bug Fixes
---------

- Fixed testing result headers inside of ``assert_resource()`` function.

2.0.6 (2018-07-06)
==================

Bug Fixes
---------

- Added using of ``result_headers`` inside of ``assert_resource`` (HOTFIX).

2.0.4 (2018-06-29)
==================

Changes
-------

- Function ``open_pyramid_request`` and ``get_pyramid_root``
  moved from ``restfw.testing`` into ``restfw.utils``
  (old versions has marked as deprecated).

2.0 (2018-06-18)
================

Features
--------

- Added ``Configurator`` directive ``add_sub_resource_fabric`` to
  register fabric of sub-resource.
- Added helper decorator ``sub_resource_config`` to declarative register
  fabric of sub-resource.
- By default all resources can have sub-resources registered by
  ``add_sub_resource_fabric`` directive or ``sub_resource_config`` decorator.
- Added JSON render adapters for ``datetime.time`` and ``enum.Enum`` types.

Backward incompatible changes
-----------------------------

- Removed interfaces ``IContainer`` and ``IHalContainerWithEmbedded``.
- Testing utility ``open_pyramid_request`` takes pyramid registry instance
  instead of pyramid configurator instance.

1.4 (2018-04-28)
================

Features
--------

- Made authorization work with broad original permissions (merged from 1.2.7).
- Added view predicates ``debug`` and ``debug_or_testing``.

Changes
-------

- Utility function ``is_testing_env()`` renamed to ``is_testing()``.

1.3 (2018-04-12)
================

Features
--------

- Removed dependency from ZODB.

1.2.7 (2018-04-26)
==================

Features
--------

- Made authorization work with broad original permissions.

1.2.4 (2018-03-15)
==================

Bug Fixes
---------

- Fixed message about error in the ``check_result_schema`` viewderiver.

1.2.2 (2018-03-15)
==================

Bug Fixes
---------

- Fixed error in ``clone_schema_class`` with cloning already cloned schemas.

1.2 (2018-03-07)
================

Features
--------

- Added support of body for DELETE requests.

1.1 (2018-03-04)
================

Features
--------

- Added into ``assert_container_listing`` support of any number of items great than 2 in container.

Changes
-------

- Refactored testing WebApp and ResourceInfo.
- Improved result validation.

1.0.2 (2018-03-01)
==================

Changes
-------

- Added checking of type of view for make decision about applying view derivers to it.

1.0 (2018-02-16)
================

Features
--------

- ``ResourceInfo`` properties replaced by methods with ``send`` argument.

0.3.2 (2018-02-08)
==================

Changes
-------

- Removed old code of generator of documentation.

0.3 (2018-02-05)
================

Features
--------

- Added support of empty values for ``IntegerNode``.

0.2.3 (2018-01-26)
==================

Changes
-------

- Fixed type hinting.

0.2 (2018-01-13)
================

Features
--------

- Added method ``http_head`` into ``Resource``.

0.1 (2017-12-21)
================

Features
--------

- First version.

