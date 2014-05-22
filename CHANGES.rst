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
* Add and remove `cache_basic` decorator to cache basic function with primitive
  typed argument. Let's focus at view level. We'll do basic decoraor later.
* Add `cache_factory` to construct a decorator to pass to `config.add_view`
  method.
* Add a cache manager which plug all components.
* Add serializers to adapt objects to store on cache
* Add Redis client for caching and versioning
* Implement master-version in redis version-store
* TODO:
  * Ability to activate / deactivate cache
  * introspectables
  * Exceptions handling
  * Tests
  * Cleanups
  * Content negociation: we should add content type in cache key.
