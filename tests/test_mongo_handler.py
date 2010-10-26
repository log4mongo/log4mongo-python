import unittest
import logging
from log4mongo.handlers import MongoHandler
from pymongo import Connection

class TestMongoHandler(unittest.TestCase):

    db_name = 'logging4mongo_test'
    cl_name = 'logs_test'

    def test_connect(self):
        handler = MongoHandler(host='localhost', database_name=self.db_name, collection=self.cl_name)
        self.assertTrue(isinstance(handler, MongoHandler))

    def test_connect_failed(self):
        try:
            handler = MongoHandler(host='uknown host', database_name=self.dn_name, collection=self.cl_name)
        except:
            return
        self.fail('MongoHandler should raise en AutoConnect Error')

    def test_emit(self):
        log     = logging.getLogger('test')
        handler = MongoHandler(host='localhost', database_name=self.db_name, collection=self.cl_name)
        log.addHandler(handler)
        log.warning('test')

        document = handler.getCollection().find_one({'message':'test', 'level' : 'WARNING'})
        self.assertEquals(document[u'message']  , 'test')
        self.assertEquals(document['level'], 'WARNING')

    def test_emit_exception(self):
        log     = logging.getLogger('test')
        handler = MongoHandler(host='localhost', database_name=self.db_name, collection=self.cl_name)
        log.addHandler(handler)

        try:
            raise Exception('exc1')
        except:
            log.exception('test')

        document = handler.getCollection().find_one({'message':'test', 'level':'ERROR'})
        self.assertEquals(document['message']  , 'test')
        self.assertEquals(document['level'], 'ERROR')
        self.assertEquals(document['exception']['message'], 'exc1')

    def test_close(self):
        handler = MongoHandler(host='localhost', database_name=self.db_name, collection=self.cl_name)
        handler.close()
        handler.getConnection().drop_database(self.db_name)


