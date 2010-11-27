import logging
from bson.timestamp import Timestamp
from pymongo import Connection

"""
// Format of LogRecord (for exception):
 {
  'lineNumber': 38,
  'exception': {
                'stactTrace': 'Traceback (most recent call last):
                               File "/var/projects/python/log4mongo-python/tests/test_mongo_handler.py", line 36, in test_emit_exception
                               raise Exception(\'exc1\')
                               Exception: exc1',
                'message': 'exc1',
                'code': 0
               },
  'thread': -1216977216,
  'level': 'ERROR',
  'timestamp': Timestamp(1290895671, 63),
  'message': 'test message',
  'fileName': '/var/projects/python/log4mongo-python/tests/test_mongo_handler.py',
  'method': 'test_emit_exception',
  'loggerName': 'testLogger'
}
"""
class MongoFormatter(logging.Formatter):
    """
    formats LogRecord into python dictionary
    """
    def format(self, record):
        document = {
            'timestamp'  : Timestamp(int(record.created), int(record.msecs)),
            'level'      : record.levelname,
            'thread'     : record.thread,
            'message'    : record.getMessage(),
            'loggerName' : record.name,
            'fileName'   : record.pathname,
            'method'     : record.funcName,
            'lineNumber' : record.lineno
        }

        if record.exc_info is not None:
            document.update({
                'exception' : {
                    'message'    : str(record.exc_info[1]),
                    'code'       : 0,
                    'stactTrace' : self.formatException(record.exc_info)
                }
            })

        return document


class MongoHandler(logging.Handler):

    """
    Setting up mongo handler,
    initializing mongodb connection via pymongo
    """
    def __init__(self, level=logging.NOTSET, host='localhost', port=27017, database_name='logging4mongo', collection='logs', username=None, password=None):
        logging.Handler.__init__(self, level)
        self.host           = host
        self.port           = port
        self.database_name  = database_name
        self.collectionName = collection
        self.username       = username
        self.password       = password

        self.connection    = None
        self.db            = None
        self.collection    = None
        self.authenticated = False

        self.formatter  = MongoFormatter()

        self._connect()

    """
    connecting to mongo databse
    """
    def _connect(self):
        self.connection = Connection(host=self.host, port=self.port)
        self.db         = self.connection[self.database_name]
        if self.username is not None and self.password is not None:
            self.authenticated = self.db.authenticate(self.username, self.password)
        self.collection = self.db[self.collectionName]

    """
    returning current handler connection
    """
    def getConnection(self):
        return self.connection

    """
    returning current handler database
    """
    def getDatabase(self):
        return self.db

    """
    returning current handler active collection
    """
    def getCollection(self):
        return self.collection


    """
    if authenticated, logging out and closing mongodb connection
    """
    def close(self):
        if self.authenticated is True:
            self.db.logout()
        if self.connection is not None:
            self.connection.disconnect()

    """
    inserting new logging record to mongo database
    """
    def emit(self, record):
        if self.collection is not None:
            try:
                self.collection.save(self.format(record))
            except:
                self.handleError(record)
