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
    write_many_method = 'insert_many'
else:
    write_method = 'save'
    write_many_method = 'insert'

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


class BufferedMongoHandler(MongoHandler):

    def __init__(self, level=logging.NOTSET, host='localhost', port=27017,
                 database_name='logs', collection='logs',
                 username=None, password=None, authentication_db='admin',
                 fail_silently=False, formatter=None, capped=False,
                 capped_max=1000, capped_size=1000000, reuse=True,
                 buffer_size=100, buffer_periodical_flush_timing=5.0,
                 buffer_early_flush_level=logging.CRITICAL, **kwargs):
        """
        Setting up buffered mongo handler, initializing mongo database connection via
        pymongo.

        This subclass aims to provide buffering mechanism to avoid hammering the database server and
        write-locking the database too often (even if mongo is performant in that matter).

        If buffer_periodical_flush_timer is set to None or 0, no periodical flush of the buffer will be done.
        It means that buffered messages might be stuck here for a while until the buffer full or
        a critical message is sent (both causing flush).

        If buffer_periodical_flush_timer is set to numeric value, a thread with timer will be launched
        to call the buffer flush periodically.
        """

        MongoHandler.__init__(self, level=level, host=host, port=port, database_name=database_name, collection=collection,
                              username=username, password=password, authentication_db=authentication_db,
                              fail_silently=fail_silently, formatter=formatter, capped=capped, capped_max=capped_max,
                              capped_size=capped_size, reuse=reuse, **kwargs)
        self.buffer = []
        self.buffer_size = buffer_size
        self.buffer_periodical_flush_timing = buffer_periodical_flush_timing
        self.buffer_early_flush_level = buffer_early_flush_level
        self.last_record = None #kept for handling the error on flush
        self.buffer_timer_thread = None

        self._buffer_lock = None
        self._timer_stopper = None

        # setup periodical flush
        if self.buffer_periodical_flush_timing:

            # clean exit event
            import atexit
            atexit.register(self.destroy)

            # retrieving main thread as a safety
            import threading
            main_thead = threading.current_thread()
            self._buffer_lock = threading.RLock()

            # call at interval function
            def call_repeatedly(interval, func, *args):
                stopped = threading.Event()

                # actual thread function
                def loop():
                    while not stopped.wait(interval) and main_thead.is_alive():  # the first call is in `interval` secs
                        func(*args)

                timer_thread = threading.Thread(target=loop, daemon=True)
                timer_thread.start()
                return stopped.set, timer_thread

            # launch thread
            self._timer_stopper, self.buffer_timer_thread = call_repeatedly(self.buffer_periodical_flush_timing, self.flush_to_mongo)

    def emit(self, record):
        """Inserting new logging record to buffer and flush if necessary."""

        self.add_to_buffer(record)

        if len(self.buffer) >= self.buffer_size or record.levelno >= self.buffer_early_flush_level:
            self.flush_to_mongo()
        return

    def buffer_lock_acquire(self):
        """Acquire lock on buffer (only if periodical flush is set)."""
        if self._buffer_lock:
            self._buffer_lock.acquire()

    def buffer_lock_release(self):
        """Release lock on buffer (only if periodical flush is set)."""
        if self._buffer_lock:
            self._buffer_lock.release()

    def add_to_buffer(self, record):
        """Add a formatted record to buffer."""

        self.buffer_lock_acquire()

        self.last_record = record
        self.buffer.append(self.format(record))

        self.buffer_lock_release()

    def flush_to_mongo(self):
        """Flush all records to mongo database."""
        if self.collection is not None and len(self.buffer) > 0:
            self.buffer_lock_acquire()
            try:

                getattr(self.collection, write_many_method)(self.buffer)
                self.empty_buffer()

            except Exception as e:
                if not self.fail_silently:
                    self.handleError(self.last_record) #handling the error on flush
            finally:
                self.buffer_lock_release()

    def empty_buffer(self):
        """Empty the buffer list."""
        del self.buffer
        self.buffer = []

    def destroy(self):
        """Clean quit logging. Flush buffer. Stop the periodical thread if needed."""
        if self._timer_stopper:
            self._timer_stopper()
        self.flush_to_mongo()
        self.close()


