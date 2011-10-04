import unittest, logging

from log4mongo.handlers import MongoHandler
from pymongo.errors import AutoReconnect

class TestMongoHandler(unittest.TestCase):
    db_name = 'log4mongo_test'
    cl_name = 'logs_test'

    def test_connect(self):
        handler = MongoHandler(host='localhost', database_name=self.db_name, collection=self.cl_name)
        self.assertTrue(isinstance(handler, MongoHandler))
        handler.close()

    def test_connect_failed(self):
        try:
            MongoHandler(host='uknown host', database_name=self.db_name, collection=self.cl_name, fail_silently=False)
        except Exception, e:
            self.assertTrue(isinstance(e, AutoReconnect))

        try:
            MongoHandler(host='uknown host', database_name=self.db_name, collection=self.cl_name, fail_silently=True)
        except Exception, e:
            self.fail("Error during conncetion shouldn't raise Exception while fail_siletnly is True")

    def test_emit(self):
        log = logging.getLogger('testLogger')
        handler = MongoHandler(host='localhost', database_name=self.db_name, collection=self.cl_name)
        log.addHandler(handler)
        log.warning('test message')

        document = handler.collection.find_one({'message': 'test message', 'level': 'WARNING'})
        self.assertEquals(document['message'], 'test message')
        self.assertEquals(document['level'], 'WARNING')
        handler.close()
        log.removeHandler(handler)

    def test_emit_exception(self):
        log = logging.getLogger('testLogger')
        handler = MongoHandler(host='localhost', database_name=self.db_name, collection=self.cl_name)
        log.addHandler(handler)

        try:
            raise Exception('exc1')
        except:
            log.exception('test message')

        document = handler.collection.find_one({'message': 'test message', 'level': 'ERROR'})
        self.assertEquals(document['message'], 'test message')
        self.assertEquals(document['level'], 'ERROR')
        self.assertEquals(document['exception']['message'], 'exc1')

        handler.close()
        log.removeHandler(handler)

    def test_emit_fail(self):
        log = logging.getLogger('testLogger')
        handler = MongoHandler(host='localhost', database_name=self.db_name, collection=self.cl_name,
                               fail_silently=True)
        log.addHandler(handler)
        handler.collection = 'meh'

        try:
            log.warning('test message')
        except Exception, e:
            self.fail("Logger shouldn't raise Exceptions (%s) while fail_silently is True." % e)

        handler.close()
        log.removeHandler(handler)

        handler = MongoHandler(host='localhost', database_name=self.db_name, collection=self.cl_name,
                               fail_silently=False)
        log.addHandler(handler)
        handler.collection = 'meh'

        try:
            log.warning('test message')
            self.fail("Logger should raise Exceptions while fail_silently is False.")
        except Exception, e:
            assert True

        handler.close()
        log.removeHandler(handler)

    def tearDown(self):
        handler = MongoHandler(host='localhost', database_name=self.db_name, collection=self.cl_name)
        handler.connection.drop_database(self.db_name)
        handler.close()
