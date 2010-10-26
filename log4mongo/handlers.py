import logging
from bson.timestamp import Timestamp
from pymongo import Connection

class MongoFormatter(logging.Formatter):
    def format(self, record):
        document = {
            u'timestamp'  : Timestamp(int(record.created), int(record.msecs)),
            u'level'      : record.levelname,
            u'thread'     : record.thread,
            u'message'    : record.getMessage(),
            u'fileName'   : record.pathname,
            u'method'     : record.funcName,
            u'lineNumber' : record.lineno,
            u'className'  : record.__class__.__name__
        }

        if record.exc_info is not None:
            document.update({
                u'exception' : {
                    u'message'    : str(record.exc_info[1]),
                    u'code'       : 0,
                    u'stactTrace' : self.formatException(record.exc_info)
                }
            })

        return document




class MongoHandler(logging.Handler):

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

    def _connect(self):
        self.connection = Connection(host=self.host, port=self.port)
        self.db         = self.connection[self.database_name]
        if self.username is not None and self.password is not None:
            self.authenticated = self.db.authenticate(self.username, self.password)
        self.collection = self.db[self.collectionName]


    def close(self):
        if self.authenticated is True:
            self.db.logout()
        if self.connection is not None:
            self.connection.disconnect()


    def emit(self, record):
        if self.collection is not None:
            try:
                self.collection.save(self.format(record))
            except:
                self.handleError(record)
