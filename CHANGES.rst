Changelog
=========

Development
-----------

* First draft of interfaces
* Add a highly not efficient implementation of a key versioner
* Add a model versioner which depends on key versioner and model identity
  inspector
* Add an example application with dummy sqla model to run tests against
* Add an sqla specific extention with hook on session events to get model
  modifications.
* Add `cache_basic` decorator to cache basic function with primitive typed
  argument.
* Add `cache_factory` to construct a decorator to pass to `config.add_view`
  method.
* TODO:

  * A cache manager utility to keep track of cached function / metrics
  * Ability to activate / deactivate cache
  * introspectables
  * Exceptions handling
  * Tests
  * Cleanups
