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

Next release
============

Bug Fixes
---------

- Do not change response with 304 status code in ``http_exception_view``.

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

