====
TODO
====

This document contains all of the things I can think of that need to be done.

Bugs
====
* mocking of udatetime.now() leaks in tests. Using the same date/time for all tests
  is OK for the time being, but it's still wrong.
* sometimes the indexes get out of sync with the main item keys. Need a check 
  script to identify/fix.

Features
========
* User management REST API
* Password reset (based on the Code base classes), and REST API,
* Activation codes (based on the Code base classes), and REST API,
* Write worker or cron job to get rid of expired codes from indices.

Enhancements
=============
* Add something node-specific to util.random_id() to help prevent collisions.
* Add something node-specific to englids to help prevent collisions.
* Logging, logging, everywhere logging.
* Document use of circus to run all of the necessary processes.

Cleanup
=======
* Move classes and schemas out of the manager modules.
* Move englids and simpleschema into their own git repos.
* Rewrite unittest tests to use pytest.