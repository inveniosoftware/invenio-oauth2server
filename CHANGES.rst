Changes
=======

Version 1.0.0b4 (released 2018-02-21)
--------------------------------------

- Refactors package.

Version 0.2.0 (released 2015-10-06)
-----------------------------------

Incompatible changes
~~~~~~~~~~~~~~~~~~~~

- Removes legacy upgrade recipes. You **MUST** upgrade to the latest
  Invenio 2.1 before upgrading Invenio-Upgrader.

Bug fixes
~~~~~~~~~

- Removes calls to PluginManager consider_setuptools_entrypoints()
  removed in PyTest 2.8.0.
- Adds missing `invenio_base` dependency.

Notes
~~~~~

- Disables test_settings_index test case.

Version 0.1.1 (released 2015-08-25)
-----------------------------------

Improved features
~~~~~~~~~~~~~~~~~

- Marks strings in templates for translations.  (#3)

Bug fixes
~~~~~~~~~

- Adds missing `invenio_upgrader` dependency and amends past upgrade
  recipes following its separation into standalone package.

Version 0.1.0 (released 2015-08-04)
-----------------------------------

- Initial public release.
