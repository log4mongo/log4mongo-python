import logging
from bson.timestamp import Timestamp
import traceback
import cStringIO
from pymongo import Connection

class MongoHandler(logging.Handler):

    def __init__(self, host='localhost', port=27017, database_name='logging4mongo', collection='logs', username=None, password=None):
        logging.Handler.__init__(self)
        self.host           = host
        self.port           = port
        self.database_name  = database_name
        self.collectionName = collection
        self.username       = username
        self.password       = password

        self.connection = None
        self.collection = None

        self._connect()

    def format(self, record):
        document = self._logRecordToDict(record)

        if record.exc_info is not None:
            document.update({
                'exception' : self._exceptionToDict(record.exc_info)
            })

        return document

    def _connect(self):
        try:
            self.connection = Connection(host=self.host, port=self.port)
            db = self.connection[self.database_name]
            if self.username is not None and self.password is not None:
                db.authenticate(self.username, self.password)
            self.collection = db[self.collectionName]
        except:
            print 'Silent handler, server connecting or collection selecting failed'

    def close(self):
        if self.connection is not None:
            self.connection.disconnect()

    def _logRecordToDict(self, record):
        return {
            'timestamp'  : Timestamp(int(record.created), int(record.msecs)),
            'level'      : record.levelname,
            'thread'     : record.thread,
            'message'    : record.getMessage(),
            'fileName'   : record.pathname,
            'method'     : record.funcName,
            'lineNumber' : record.lineno,
            'className'  : record.__class__.__name__
        }

    def _exceptionToDict(self, e):
        sio = cStringIO.StringIO()
        traceback.print_exception(e[0], e[1], e[2], None, sio)
        s = sio.getvalue()
        sio.close()
        if s[-1:] == "\n":
            s = s[:-1]

        return {
            'message'    : str(e[1]),
            'code'       : 0,
            'stactTrace' : s
        }




    def emit(self, record):
        if self.collection is not None:
            try:
                self.collection.save(self.format(record))
            except:
                self.handleError(record)


if __name__ == '__main__':
    log = logging.getLogger('')
    log.addHandler(logging.StreamHandler())
    log.addHandler(MongoHandler())


    def test():
        try:
            raise Exception('test', 'test1')
        except Exception:
            log.exception('exception catched')
            pass

    test()


