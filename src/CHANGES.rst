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
        - Breaking Changes
        - Docs

CHANGELOG
*********

Next release
============

Bug Fixes
---------

- Fixed assertion of headers from HEAD and GET responses.

8.0.2 (2022-01-14)
==================

Bug Fixes
---------

- Added root instance into request before ``RootCreated`` event will
  be sent.

8.0 (2021-12-09)
================

Features
--------

- Added support of ``pyramid 2+``.

Breaking Changes
----------------

- Dropped support of ``pyramid < 2.0``:

    - ``RestACLAuthorizationPolicy`` removed. You can use ``RestAclHelper``
      to write implementation of ``ISecurityPolicy``. See
      `"Upgrading Authentication/Authorization" <https://docs.pylonsproject.org/projects/pyramid/en/latest/whatsnew-2.0.html#upgrading-auth-20>`_
      in Pyramid documentation. Also you can use ``TestingSecurityPolicy``
      as example of implementation of ``ISecurityPolicy``.

7.0.6 (2021-06-22)
==================

Bug Fixes
---------

- Fixed handling of ``JSONDecodeError`` in ``get_input_data()`` function (merged from v6.0.6).

7.0.2 (2021-06-03)
==================

Bug Fixes
---------

- Replaced import from ``webtest`` onto import from ``webob`` in ``usage_examples`` module.

7.0 (2021-06-02)
================

Features
--------

- Added method ``UsageExamples.send()`` to replace argument ``send``
  of ``UsageExamples.<method>_requests()`` methods.
- Method ``UsageExamples.send()`` returns instance of ``TestResponse``.
- Added support of type-hint for ``__parent__`` field of classes and ``parent`` argument
  of functions decorated by ``sub_resource_config()`` instead of specify
  parent type as the decorator's argument.

Breaking Changes
----------------

- Removed argument ``send`` from all ``UsageExamples.<method>_requests()`` methods.
- Version of ``Sphinx`` updated to 4.x.

6.0.6 (2021-06-22)
==================

Bug Fixes
---------

- Fixed handling of ``JSONDecodeError`` in ``get_input_data()`` function.

6.0.4 (2021-03-30)
==================

Bug Fixes
---------

- Fixed authorization policy to support ACL rules to allow or
  deny requests with concrete http-method.

6.0.2 (2021-03-23)
==================

Changes
-------

- Removed parameter ``total_count`` from links named ``next`` and ``prev``.

6.0 (2021-03-18)
================

Features
--------

- Added a new abstraction layer ``IResourceView`` as separate from resource component.
  All HTTP-related code moved from resources into this layer.
- Added configurator directive ``add_resource_view()`` and corresponding decorator
  ``resource_view_config()``.
- Added a new exception ``ParametersError`` for use it in a resource code
  instead of  ``create_validation_error()`` function.
- Added function ``create_multi_validation_error()`` for create ``ValidationError``
  with many nodes.
- Added a new optional argument ``json_encoder`` for ``WebApp`` class.
- Added function ``get_resource_view()`` for getting instance of resource view
  corresponding to given resource and request instance.

Changes
-------

- Removed ``check_request_method_view`` viewderiver.

Breaking Changes
----------------

- Module ``restfw.config`` replaced by package ``restfw.config`` with separate modules
  for each configurator directive.
- Helper decorators for configurator moved from ``restfw.config`` into other
  modules (``.resources`` and ``.external_links``).
- Methods ``__json__()``, ``as_dict()``, ``get_allowed_methods()``, ``http_options()``,
  ``http_head()``, ``http_get`` of ``IResource`` and properties like
  ``options_for_*`` moved into ``IResourceView``.
- Methods ``as_embedded()``, ``get_links()`` of ``IHalResource`` moved
  into ``IHalResourceView``.
- Method ``get_embedded()`` of ``IHalResourceWithEmbedded`` moved
  into ``IHalResourceWithEmbeddedView``.
- Removed class ``HalResourceWithEmbedded`` (you must use view
  ``HalResourceWithEmbeddedView`` instead).

5.2 (2020-12-09)
================

Features
--------

- For ``DateTimeNode`` added arguments ``default_tzinfo`` and ``dt_format``
  with ``None`` as default value.

5.1.2 (2020-11-20)
==================

Bug Fixes
---------

- Fixed converting ```EmbeddedResources`` instance into dictionary
  for JSON encoding.

5.1 (2020-10-30)
================

Features
--------

- Added subscriber predicates ``testing``, ``debug`` and ``debug_or_testing``.

5.0 (2020-10-29)
================

Features
--------

- Added support of different package prefixes for ``RstDocGenerator``.

Backward Incompatible Changes
-----------------------------

- Dropped support of Python 2 and 3.5.
- Argument ``app_prefix`` of ``RstDocGenerator`` class replaced by ``package_prefixes``.

4.2 (2020-10-06)
================

Features
--------

- Added function ``add_adapter_into_json_renderer`` to add
  custom adapters for JSON-renderer.
- Added argument ``path`` into ``open_pyramid_request()``.

Changes
-------

- JSON-renderer configured to produce UTF-8 JSON.

4.1.4 (2020-08-06)
==================

Bug Fixes
---------

- Fixed errors with nullable ``StringNode`` and ``EmptyStringNode``.

4.1.2 (2020-08-06)
==================

Changes
-------

- Added testing fixture ``pyramid_settings`` for change
  pyramid's settings in tests.

4.1 (2020-07-29)
================

Features
--------

- Added method ``Resource.get_etag()`` and response header ``ETag``.
- Added support of conditional requests with headers ``If-Match``
  and ``If-None-Match``.
- Added schema ``GetNextPageSchema`` and basic support of cursor
  based pagination.

Changes
-------

- Method ``HalResource.__json__()`` don't overwrite a links,
  added by ``HalResource.get_links()`` method.

4.0 (2020-06-10)
================

Features
--------

- Added configurator directives ``add_external_link_fabric`` and
  ``add_external_link_fabric_predicate``.
- Added decorator ``restfw.config.external_link_config`` to
  declarative registration of fabric of external link.
- Added method ``Resource.get_registry()``.
- Added to all schema-nodes argument ``nullable``.
- Added support of ``nullable`` nodes into ``colander2jsonschema`` converter.

Backward Incompatible Changes
-----------------------------

- Removed method ``Resource.get_request()``.
- Removed method ``Root.get_request()``.
- Added method ``Root.__init__(registry)``.

3.7 (2020-03-24)
================

Features
--------

- Added new filed ``default_auth`` and method ``authorize_request`` into
  ``UsageExamples`` class.
- Added argument ``auth`` into objects that provides ``ISendTestingRequest``
  (for example ``send`` function used in usage examples).

Changes
-------

- Deprecated field ``headers_for_listing`` of ``UsageExamples`` class.

3.6 (2020-03-23)
================

Features
--------

- Added validators ``LazyAll`` and ``LazyAny``.

Bug Fixes
---------

- Fixed using URLs with unicode chars for send requests
  with help of ``WebApp`` under Python 3.

3.5.2 (2020-03-23)
==================

Bug Fixes
---------

- Fixed dependencies constraints in ``setup.py``.

3.5 (2020-02-26)
================

Features
--------

- Added argument ``exclude_from_doc`` for function ``send()`` used inside of ``Usage Examples``.
- Documentation generator not include examples with ``exclude_from_doc == True``.

3.4 (2019-12-27)
================

Features
--------

- Added argument ``description`` for function ``send()`` used inside of ``Usage Examples``.
- Documentation generator include only first example request from all of with equal
  ``status code`` and not empty ``description``.

Bug Fixes
---------

- Added encoding of class name in function ``clone_schema_class`` for Python 2.
- Disabled view deriver ``check_request_method_view`` and ``check_result_schema``
  for custom named views for resource.

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

