from log4mongo.handlers import MongoHandler
from pymongo.errors import AutoReconnect
from StringIO import StringIO
import unittest
import logging
import sys


class TestMongoHandler(unittest.TestCase):
    host_name = 'localhost'
    database_name = 'log4mongo_test'
    collection_name = 'logs_test'

    def setUp(self):
        self.handler = MongoHandler(host=self.host_name, database_name=self.database_name, collection=self.collection_name)
        self.log = logging.getLogger('testLogger')
        self.log.addHandler(self.handler)
        self.old_stderr = sys.stdout
        sys.stderr = StringIO()

    def tearDown(self):
        self.handler.connection.drop_database(self.database_name)
        self.handler.close()
        self.log.removeHandler(self.handler)
        self.log = None
        self.handler = None
        sys.stderr.close()
        sys.stderr = self.old_stderr

    def test_connect(self):
        handler = MongoHandler(host='localhost', database_name=self.database_name, collection=self.collection_name)
        self.assertTrue(isinstance(handler, MongoHandler))
        self.handler.connection.drop_database(self.database_name)
        handler.close()

    def test_connect_failed(self):
        with self.assertRaises(AutoReconnect):
            MongoHandler(host='unknow_host', database_name=self.database_name, collection=self.collection_name)

    def test_connect_failed_silent(self):
        handler = MongoHandler(host='unknow_host', database_name=self.database_name, collection=self.collection_name, fail_silently=True)
        self.assertTrue(isinstance(handler, MongoHandler))
        self.handler.connection.drop_database(self.database_name)
        handler.close()

    def test_emit(self):
        self.log.warning('test message')
        document = self.handler.collection.find_one({'message': 'test message', 'level': 'WARNING'})
        self.assertEquals(document['message'], 'test message')
        self.assertEquals(document['level'], 'WARNING')

    def test_emit_exception(self):
        try:
            raise Exception('exc1')
        except:
            self.log.exception('test message')

        document = self.handler.collection.find_one({'message': 'test message', 'level': 'ERROR'})
        self.assertEquals(document['message'], 'test message')
        self.assertEquals(document['level'], 'ERROR')
        self.assertEquals(document['exception']['message'], 'exc1')

    def test_emit_fail(self):
        self.handler.collection = ''
        self.log.warn('test warning')
        self.assertRegexpMatches(sys.stderr.getvalue(), r"AttributeError: 'str' object has no attribute 'save'")

    def test_email_fail_silend(self):
        self.handler.fail_silently = True
        self.handler.collection = ''
        self.log.warn('test warming')
        self.assertEqual(sys.stderr.getvalue(), '')