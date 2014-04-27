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
