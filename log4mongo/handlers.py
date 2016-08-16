import datetime as dt
import logging

try:
    from pymongo import MongoClient as Connection
except ImportError:
    from pymongo import Connection

from pymongo.collection import Collection
from pymongo.errors import OperationFailure, PyMongoError
import pymongo
if pymongo.version_tuple[0] >= 3:
    from pymongo.errors import ServerSelectionTimeoutError
    write_method = 'insert_one'
else:
    write_method = 'save'

"""
Example format of generated bson document:
{
    'thread': -1216977216,
    'threadName': 'MainThread',
    'level': 'ERROR',
    'timestamp': datetime.datetime(2016, 8, 16, 15, 20, 24, 794341),
    'message': 'test message',
    'module': 'test_module',
    'fileName': '/var/projects/python/log4mongo-python/tests/test_handlers.py',
    'lineNumber': 38,
    'method': 'test_emit_exception',
    'loggerName':  'testLogger',
    'exception': {
        'stackTrace': 'Traceback (most recent call last):
                       File "/var/projects/python/log4mongo-python/tests/\
                           test_handlers.py", line 36, in test_emit_exception
                       raise Exception(\'exc1\')
                       Exception: exc1',
        'message': 'exc1',
        'code': 0
    }
}
"""
_connection = None


class MongoFormatter(logging.Formatter):

    DEFAULT_PROPERTIES = logging.LogRecord(
        '', '', '', '', '', '', '', '').__dict__.keys()

    def format(self, record):
        """Formats LogRecord into python dictionary."""
        # Standard document
        document = {
            'timestamp': dt.datetime.utcnow(),
            'level': record.levelname,
            'thread': record.thread,
            'threadName': record.threadName,
            'message': record.getMessage(),
            'loggerName': record.name,
            'fileName': record.pathname,
            'module': record.module,
            'method': record.funcName,
            'lineNumber': record.lineno
        }
        # Standard document decorated with exception info
        if record.exc_info is not None:
            document.update({
                'exception': {
                    'message': str(record.exc_info[1]),
                    'code': 0,
                    'stackTrace': self.formatException(record.exc_info)
                }
            })
        # Standard document decorated with extra contextual information
        if len(self.DEFAULT_PROPERTIES) != len(record.__dict__):
            contextual_extra = set(record.__dict__).difference(
                set(self.DEFAULT_PROPERTIES))
            if contextual_extra:
                for key in contextual_extra:
                    document[key] = record.__dict__[key]
        return document


class MongoHandler(logging.Handler):

    def __init__(self, level=logging.NOTSET, host='localhost', port=27017,
                 database_name='logs', collection='logs',
                 username=None, password=None, authentication_db='admin',
                 fail_silently=False, formatter=None, capped=False,
                 capped_max=1000, capped_size=1000000, reuse=True, **kwargs):
        """
        Setting up mongo handler, initializing mongo database connection via
        pymongo.

        If reuse is set to false every handler will have it's own MongoClient.
        This could hammer down your MongoDB instance, but you can still use
        this option.

        The default is True. As such a program with multiple handlers
        that log to mongodb will have those handlers share a single connection
        to MongoDB.
        """
        logging.Handler.__init__(self, level)
        self.host = host
        self.port = port
        self.database_name = database_name
        self.collection_name = collection
        self.username = username
        self.password = password
        self.authentication_database_name = authentication_db
        self.fail_silently = fail_silently
        self.connection = None
        self.db = None
        self.collection = None
        self.authenticated = False
        self.formatter = formatter or MongoFormatter()
        self.capped = capped
        self.capped_max = capped_max
        self.capped_size = capped_size
        self.reuse = reuse
        self._connect(**kwargs)

    def _connect(self, **kwargs):
        """Connecting to mongo database."""
        global _connection
        if self.reuse and _connection:
            self.connection = _connection
        else:
            if pymongo.version_tuple[0] < 3:
                try:
                    self.connection = Connection(host=self.host,
                                                 port=self.port, **kwargs)
                # pymongo >= 3.0 does not raise this error
                except PyMongoError:
                    if self.fail_silently:
                        return
                    else:
                        raise
            else:
                self.connection = Connection(host=self.host, port=self.port,
                                             **kwargs)
                try:
                    self.connection.is_locked
                except ServerSelectionTimeoutError:
                    if self.fail_silently:
                        return
                    else:
                        raise
            _connection = self.connection

        self.db = self.connection[self.database_name]
        if self.username is not None and self.password is not None:
            auth_db = self.connection[self.authentication_database_name]
            self.authenticated = auth_db.authenticate(self.username,
                                                      self.password)

        if self.capped:
            #
            # We don't want to override the capped collection
            # (and it throws an error anyway)
            try:
                self.collection = Collection(self.db, self.collection_name,
                                             capped=True, max=self.capped_max,
                                             size=self.capped_size)
            except OperationFailure:
                # Capped collection exists, so get it.
                self.collection = self.db[self.collection_name]
        else:
            self.collection = self.db[self.collection_name]

    def close(self):
        """
        If authenticated, logging out and closing mongo database connection.
        """
        if self.authenticated:
            self.db.logout()
        if self.connection is not None:
            self.connection.close()

    def emit(self, record):
        """Inserting new logging record to mongo database."""
        if self.collection is not None:
            try:
                getattr(self.collection, write_method)(self.format(record))
            except Exception:
                if not self.fail_silently:
                    self.handleError(record)

    def __exit__(self, type, value, traceback):
        self.close()
