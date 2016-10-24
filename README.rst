log4mongo-python
================
log4mongo-python is mongo database handler for python logging, part of log4mongo.org project.
log4mongo-python is using pymongo driver - http://github.com/mongodb/mongo-python-driver


Requirements
------------

- python 2.7+
- pymongo 2.8+
- mongo database

For more information see *debian_requirements.txt* and *requirements.txt* files.

Configuration
-------------

Example handler python configuration: ::

 import logging
 from log4mongo.handlers import MongoHandler

 logger = logging.getLogger('test')
 logger.addHandler(MongoHandler(host='localhost'))
 logger.warning('test')


Contextual information
----------------------

It is possible to decorate you document with contextual information. There are tow approaches.

**1.) approach**
::

 import logging
 from log4mongo.handlers import MongoHandler

 handler = MongoHandler(host='localhost')
 logger = logging.getLogger('test')
 logger.addHandler(handler)
 logging.LoggerAdapter(logger, {'ip': '127.0.0.1'}).info('test')

**2.) approach**
::

 import logging
 from log4mongo.handlers import MongoHandler

 handler = MongoHandler(host='localhost')
 logger = logging.getLogger('test')
 logger.addHandler(handler)
 logger.info('test', extra={'ip': '127.0.0.1'})


As you can see, second approach is more straightforward and there is no need to use LoggerAdapter.


Capped collections
------------------

Capped collections are fixed-size collections that support high-throughput operations that insert, retrieve,
and delete documents based on insertion order. Capped collections work in a way similar
to circular buffers: once a collection fills its allocated space, it makes room for new documents
by overwriting the oldest documents in the collection.

Before switching to capped collections, read this document please: http://docs.mongodb.org/manual/core/capped-collections/

This behaviour is disabled by default. You can enable this behaviour in constructor with *capped=True*:
::

 import logging
 from log4mongo.handlers import MongoHandler

 handler = MongoHandler(host='localhost', capped=True)


Buffered handler
----------------

BufferedMongoHandler is a subclass of MongoHandler allowing to buffer log messages
 and write them all at once to the database. The goal is to avoid too many writes to the database, thus avoiding
 too frequent write-locks.
Log message buffer flush happens when the buffer is full, when a critical log message is emitted, and also periodically.
An early buffer flush can happen when a critical message is emitted.
And in order to avoid messages to stay indefinitively in the buffer queue before appearing in database, a periodical
 flush happens every X seconds.

This periodical flush can also be deactivated with *buffer_periodical_flush_timing=False*,
 thus avoiding the timer thread to be created.

Buffer size is configurable, as well as the log level for early flush (default is CRITICAL).
::

 import logging
 from log4mongo.handlers import BufferedMongoHandler

 handler = BufferedMongoHandler(host='localhost',                          # All usual MongoHandler parameters are valid
                                capped=True,
                                buffer_size=100,                           # buffer size.
                                buffer_periodical_flush_timing=10.0,       # periodical flush every 10 seconds
                                buffer_early_flush_level=logging.CRITICAL) # early flush level

 logger = logging.getLogger().addHandler(handler)


Example using full function signature
-------------------------------------
Here is an example call with all parameters filled:
::

 import logging
 from log4mongo.handlers import MongoHandler

 handler = MongoHandler(
     level=logging.INFO,
     host='localhost',
     port=27017,
     database_name='my_database',
     collection='logs',
     username='my_user',
     password='my_password',
     authentication_db='admin',
     fail_silently=False,
     formatter=None,
     capped=False,
     capped_max=1000,
     capped_size=1000000,
     reuse=True,
 )

 logger = logging.getLogger().addHandler(handler)


Tests
-----

** Tested on evnironment **

- Ubuntu 14.04
- python 2.7.4
- pymongo >2.8.3
- mongod - db version v3.0.2
- python unittest

**Running tests**

Before you run the test you must start mongo database. You will do so by this command: ::

 $ mongod --dbpath /tmp/


To run the test run command: ::

 $ python test.py
 $ python setup.py test


See vagrant file to quickly setup the test environment.

Original Author
---------------

| char0n (Vladimír Gorej, CodeScale s.r.o.) 
| email: gorej@codescale.net
| web: http://www.codescale.net

Current Maitainer
-----------------
| Oz Nahum Tiram
| email: nahumoz@gmail.com
| web: oz123.github.io

References
----------
- http://www.mongodb.org/
- http://docs.python.org/library/logging.html
- http://github.com/mongodb/mongo-python-driver
- http://log4mongo.org
