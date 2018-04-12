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

1.3 (2018-04-12)
================

Features
--------

- Removed dependency from ZODB.

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

