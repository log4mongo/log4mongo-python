from bson.timestamp import Timestamp
from pymongo import Connection
from pymongo.collection import Collection
from pymongo.errors import AutoReconnect, OperationFailure
import logging

"""
Example format of generated bson document:
{
    'thread': -1216977216,
    'level': 'ERROR',
    'timestamp': Timestamp(1290895671, 63),
    'message': 'test message',
    'fileName': '/var/projects/python/log4mongo-python/tests/test_mongo_handler.py',
    'lineNumber': 38,
    'method': 'test_emit_exception',
    'loggerName':  'testLogger',
    'exception': {
        'stackTrace': 'Traceback (most recent call last):
                       File "/var/projects/python/log4mongo-python/tests/test_mongo_handler.py", line 36, in test_emit_exception
                       raise Exception(\'exc1\')
                       Exception: exc1',
        'message': 'exc1',
        'code': 0
    }
}
"""

logging.LogRecord

class MongoFormatter(logging.Formatter):

    DEFAULT_PROPERTIES = logging.LogRecord('', '', '', '', '', '', '', '').__dict__.keys()

    def format(self, record):
        """Formats LogRecord into python dictionary."""
        # Standard document
        document = {
            'timestamp': Timestamp(int(record.created), int(record.msecs)),
            'level': record.levelname,
            'thread': record.thread,
            'message': record.getMessage(),
            'loggerName': record.name,
            'fileName': record.pathname,
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
            contextual_extra = set(record.__dict__).difference(set(self.DEFAULT_PROPERTIES))
            if contextual_extra:
                for key in contextual_extra:
                    document[key] = record.__dict__[key]
        return document


class MongoHandler(logging.Handler):

    def __init__(self, level=logging.NOTSET, host='localhost', port=27017, database_name='logs', collection='logs',
                 username=None, password=None, fail_silently=False, formatter=None, capped=False, capped_max=1000, capped_size=1000000):
        """Setting up mongo handler, initializing mongo database connection via pymongo."""
        logging.Handler.__init__(self, level)
        self.host = host
        self.port = port
        self.database_name = database_name
        self.collection_name = collection
        self.username = username
        self.password = password
        self.fail_silently = fail_silently
        self.connection = None
        self.db = None
        self.collection = None
        self.authenticated = False
        self.formatter = formatter or MongoFormatter()
        self.capped = capped
        self.capped_max = capped_max
        self.capped_size = capped_size
        self._connect()

    def _connect(self):
        """Connecting to mongo database."""

        try:
            self.connection = Connection(host=self.host, port=self.port)
        except AutoReconnect, e:
            if self.fail_silently:
                return
            else:
                raise AutoReconnect(e)

        self.db = self.connection[self.database_name]
        if self.username is not None and self.password is not None:
            self.authenticated = self.db.authenticate(self.username, self.password)
            
    	if self.capped:
            try: #we don't want to override the capped collection (and it throws an error anyway)
                self.collection = Collection(self.db, self.collection_name, capped=True, max=self.capped_max, size=self.capped_size)
            except OperationFailure:
                pass
        else:
            self.collection = self.db[self.collection_name]

    def close(self):
        """If authenticated, logging out and closing mongo database connection."""
        if self.authenticated:
            self.db.logout()
        if self.connection is not None:
            self.connection.disconnect()

    def emit(self, record):
        """Inserting new logging record to mongo database."""
        if self.collection is not None:
            try:
                self.collection.save(self.format(record))
            except Exception:
                if not self.fail_silently:
                    self.handleError(record) 
