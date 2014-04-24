Changelog
=========

Development
-----------

* First draft of interfaces
* Add a highly not efficient implementation of a key versioner
* Add a model versioner which depends on key versioner and model identity
  inspector
* TODO:

  * A pyramid example app with dummy sqla model;
  * sqla specific extention with hook on session events to get model
    modifications.
  * Plumbing components
  * Tests, tests and tests