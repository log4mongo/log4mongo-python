from log4mongo.handlers import BufferedMongoHandler, MongoHandler, write_method, write_many_method
import log4mongo.handlers
from pymongo.errors import PyMongoError
import pymongo
if pymongo.version_tuple[0] >= 3:
    from pymongo.errors import ServerSelectionTimeoutError

try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO

import unittest
import logging
import time
import sys


class TestMongoHandler(unittest.TestCase):
    host_name = 'localhost'
    database_name = 'log4mongo_test'
    collection_name = 'logs_test'

    def setUp(self):
        self.handler = MongoHandler(host=self.host_name,
                                    database_name=self.database_name,
                                    collection=self.collection_name,
                                    )
        self.log = logging.getLogger('testLogger')
        self.log.setLevel(logging.DEBUG)
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
        handler = MongoHandler(host='localhost',
                               database_name=self.database_name,
                               collection=self.collection_name)
        self.assertTrue(isinstance(handler, MongoHandler))
        self.handler.connection.drop_database(self.database_name)
        handler.close()

    def test_1_connect_failed(self):
        log4mongo.handlers._connection = None
        kwargs = {'connectTimeoutMS': 2000, 'serverselectiontimeoutms': 2000}
        if pymongo.version_tuple[0] < 3:
            with self.assertRaises(PyMongoError):
                MongoHandler(host='unknow_host',
                             database_name=self.database_name,
                             collection=self.collection_name,
                             **kwargs)
        else:
            with self.assertRaises(ServerSelectionTimeoutError):
                MongoHandler(host='unknow_host',
                             database_name=self.database_name,
                             collection=self.collection_name,
                             **kwargs)

    def test_connect_failed_silent(self):
        log4mongo.handlers._connection = None
        kwargs = {'connectTimeoutMS': 2000, 'serverselectiontimeoutms': 2000}
        handler = MongoHandler(host='unknow_host',
                               database_name=self.database_name,
                               collection=self.collection_name,
                               fail_silently=True,
                               **kwargs)
        self.assertTrue(isinstance(handler, MongoHandler))
        self.handler.connection.drop_database(self.database_name)
        handler.close()

    def test_emit(self):
        self.log.warning('test message')
        document = self.handler.collection.find_one(
            {'message': 'test message', 'level': 'WARNING'})
        self.assertEqual(document['message'], 'test message')
        self.assertEqual(document['level'], 'WARNING')

    def test_emit_exception(self):
        try:
            raise Exception('exc1')
        except:
            self.log.exception('test message')

        document = self.handler.collection.find_one(
            {'message': 'test message', 'level': 'ERROR'})
        self.assertEqual(document['message'], 'test message')
        self.assertEqual(document['level'], 'ERROR')
        self.assertEqual(document['exception']['message'], 'exc1')

    def test_emit_fail(self):
        self.handler.collection = ''
        self.log.warning('test warning')
        val = sys.stderr.getvalue()
        self.assertRegexpMatches(val, r"AttributeError: 'str' object has no attribute '{}'".format(write_method))

    def test_email_fail_silent(self):
        self.handler.fail_silently = True
        self.handler.collection = ''
        self.log.warning('test warming')
        self.assertEqual(sys.stderr.getvalue(), '')

    def test_contextual_info(self):
        self.log.info('test message with contextual info',
                      extra={'ip': '127.0.0.1', 'host': 'localhost'})
        document = self.handler.collection.find_one(
            {'message': 'test message with contextual info', 'level': 'INFO'})
        self.assertEqual(document['message'],
                         'test message with contextual info')
        self.assertEqual(document['level'], 'INFO')
        self.assertEqual(document['ip'], '127.0.0.1')
        self.assertEqual(document['host'], 'localhost')

    def test_contextual_info_adapter(self):
        adapter = logging.LoggerAdapter(self.log,
                                        {'ip': '127.0.0.1',
                                         'host': 'localhost'})
        adapter.info('test message with contextual info')
        document = self.handler.collection.find_one({'message': 'test message with contextual info', 'level': 'INFO'})
        self.assertEqual(document['message'], 'test message with contextual info')
        self.assertEqual(document['level'], 'INFO')
        self.assertEqual(document['ip'], '127.0.0.1')
        self.assertEqual(document['host'], 'localhost')


class TestCappedMongoHandler(TestMongoHandler):

    capped_max = 10

    def setUp(self):
        self.handler = MongoHandler(host=self.host_name, database_name=self.database_name,
                                    collection=self.collection_name, capped=True, capped_max=self.capped_max)
        self.log = logging.getLogger('testLogger')
        self.log.setLevel(logging.DEBUG)
        self.log.addHandler(self.handler)
        self.old_stderr = sys.stdout
        sys.stderr = StringIO()

    def test_capped(self):
        options = self.handler.db.command('collstats', self.collection_name)
        self.assertEqual(options['max'], 10)
        self.assertEqual(options['capped'], 1)

    def test_capped_max(self):
        for i in range(self.capped_max * 2):
            self.log.info('test capped info')
        documents = self.handler.collection.find()
        self.assertEqual(documents.count(), 10)

    def test_override_no_capped_collection(self):
        # Creating no capped handler
        self.handler_no_capped = MongoHandler(host=self.host_name,
                                              database_name=self.database_name,
                                              collection=self.collection_name)
        self.log.removeHandler(self.handler)
        self.log.addHandler(self.handler_no_capped)
        self.log.info('test info')
        # Creating capped handler
        self.handler_capped = MongoHandler(host=self.host_name,
                                           database_name=self.database_name,
                                           collection=self.collection_name,
                                           capped=True,
                                           capped_max=self.capped_max)
        self.log.addHandler(self.handler)
        self.log.info('test info')

    def test_override_capped_collection(self):
        # Creating capped handler
        self.handler_capped = MongoHandler(
            host=self.host_name, database_name=self.database_name,
            collection=self.collection_name, capped=True,
            capped_max=self.capped_max)
        self.log.removeHandler(self.handler)
        self.log.addHandler(self.handler)
        self.log.info('test info')
        # Creating no capped handler
        self.handler_no_capped = MongoHandler(host=self.host_name,
                                              database_name=self.database_name,
                                              collection=self.collection_name)
        self.log.addHandler(self.handler_no_capped)
        self.log.info('test info')

    def test_emit_on_reconnect_existing_capped_collection(self):
        self.log.removeHandler(self.handler)
        handler = MongoHandler(host=self.host_name, database_name=self.database_name,
                                    collection=self.collection_name, capped=True, capped_max=self.capped_max)
        self.log.addHandler(handler)

        self.log.warning('test message')
        document = handler.collection.find_one({'message': 'test message', 'level': 'WARNING'})
        self.assertEqual(document['message'], 'test message')
        self.assertEqual(document['level'], 'WARNING')


class TestBufferedMongoHandler(TestMongoHandler):
    collection_name = 'buffered_logs_test'

    def setUp(self):
        self.handler = BufferedMongoHandler(host=self.host_name,
                                    database_name=self.database_name,
                                    collection=self.collection_name,
                                    buffer_size=5, buffer_periodical_flush_timing=None,
                                    buffer_early_flush_level=logging.CRITICAL
                                    )
        self.log = logging.getLogger('testLogger')
        self.log.setLevel(logging.DEBUG)
        self.log.addHandler(self.handler)
        self.old_stderr = sys.stdout
        sys.stderr = StringIO()

    def force_flush(self):
        self.handler.flush_to_mongo()

    def test_contextual_info(self):
        self.log.info('test message with contextual info',
                      extra={'ip': '127.0.0.1', 'host': 'localhost'})
        self.force_flush()
        document = self.handler.collection.find_one(
            {'message': 'test message with contextual info', 'level': 'INFO'})
        self.assertEqual(document['message'],
                         'test message with contextual info')
        self.assertEqual(document['level'], 'INFO')
        self.assertEqual(document['ip'], '127.0.0.1')
        self.assertEqual(document['host'], 'localhost')

    def test_contextual_info_adapter(self):
        adapter = logging.LoggerAdapter(self.log,
                                        {'ip': '127.0.0.1',
                                         'host': 'localhost'})
        adapter.info('test message with contextual info')
        self.force_flush()
        document = self.handler.collection.find_one(
            {'message': 'test message with contextual info', 'level': 'INFO'})
        self.assertEqual(document['message'], 'test message with contextual info')
        self.assertEqual(document['level'], 'INFO')
        self.assertEqual(document['ip'], '127.0.0.1')
        self.assertEqual(document['host'], 'localhost')

    def test_emit(self):
        self.log.warning('test message')
        self.force_flush()
        document = self.handler.collection.find_one(
            {'message': 'test message', 'level': 'WARNING'})
        self.assertEqual(document['message'], 'test message')
        self.assertEqual(document['level'], 'WARNING')

    def test_emit_exception(self):
        try:
            raise Exception('exc1')
        except:
            self.log.exception('test message')
        self.force_flush()

        document = self.handler.collection.find_one(
            {'message': 'test message', 'level': 'ERROR'})
        self.assertEqual(document['message'], 'test message')
        self.assertEqual(document['level'], 'ERROR')
        self.assertEqual(document['exception']['message'], 'exc1')

    def test_emit_fail(self):
        self.handler.collection = ''
        self.log.warn('test warning')
        self.force_flush()
        val = sys.stderr.getvalue()
        self.assertRegexpMatches(val, r"AttributeError: 'str' object has no attribute '{}'".format(write_many_method))

    def test_buffer(self):
        self.force_flush()
        self.assertEqual(len(self.handler.buffer), 0, "Ensure buffer should be empty")

        self.log.warning('test_buffer message')

        document = self.handler.collection.find_one({'message': 'test_buffer message'})
        self.assertIsNone(document, "Should not have been written to database")
        self.assertEqual(len(self.handler.buffer), 1, "Buffer size should be 1")

        self.log.info('test_buffer message')
        self.log.debug('test_buffer message')
        self.log.info('test_buffer message')

        doc_amount = self.handler.collection.find({'message': 'test_buffer message'}).count()
        self.assertEqual(doc_amount, 0, "Nothing should have been written to database")
        self.assertEqual(len(self.handler.buffer), 4, "Buffer size should be 4")

        self.log.warning('test_buffer message')

        doc_amount = self.handler.collection.find({'message': 'test_buffer message'}).count()

        self.assertEqual(doc_amount, 5, "Buffer size reached, buffer should have been written to database")
        self.assertEqual(len(self.handler.buffer), 0, "Ensure buffer should be empty")

        self.log.warning('test_buffer message 2')

        document = self.handler.collection.find_one({'message': 'test_buffer message 2'})
        self.assertIsNone(document, 'Should not have been written to database')
        self.assertEqual(len(self.handler.buffer), 1, "Buffer size should be 1")

    def test_buffer_early_flush(self):
        self.force_flush()
        self.assertEqual(len(self.handler.buffer), 0, "Ensure buffer should be empty")

        self.log.info('test_buffer_early_flush message')

        document = self.handler.collection.find_one({'message': 'test_buffer_early_flush message'})
        self.assertIsNone(document, "Should not have been written to database")
        self.assertEqual(len(self.handler.buffer), 1, "Buffer size should be 1")

        self.log.critical('test_buffer_early_flush message')
        doc_amount = self.handler.collection.find({'message': 'test_buffer_early_flush message'}).count()
        self.assertEqual(doc_amount, 2, "2 messages should have been written to database")
        self.assertEqual(len(self.handler.buffer), 0, "Buffer should now be empty")

        doc_amount = self.handler.collection.find({'message': 'test_buffer_early_flush message',
                                                     'level': 'INFO'}).count()
        self.assertEqual(doc_amount, 1, "One INFO message should have been written to database")

        doc_amount = self.handler.collection.find({'message': 'test_buffer_early_flush message',
                                                     'level': 'CRITICAL'}).count()
        self.assertEqual(doc_amount, 1, "One CRITICAL message should have been written to database")

    def test_buffer_periodical_flush(self):

        # Creating capped handler
        self.handler_periodical = BufferedMongoHandler(host=self.host_name,
                                                       database_name=self.database_name,
                                                       collection=self.collection_name,
                                                       buffer_size=5, buffer_periodical_flush_timing=2.0,
                                                       buffer_early_flush_level=logging.CRITICAL)
        self.log.removeHandler(self.handler)
        self.log.addHandler(self.handler_periodical)

        self.log.info('test periodical buffer')
        document = self.handler_periodical.collection.find_one({'message': 'test periodical buffer'})
        self.assertIsNone(document, "Should not have been written to database")  # except if your computer is really slow
        self.assertEqual(len(self.handler_periodical.buffer), 1, "Buffer size should be 1")

        self.log.info('test periodical buffer')
        document = self.handler_periodical.collection.find_one({'message': 'test periodical buffer'})
        self.assertIsNone(document, "Should not have been written to database")
        self.assertEqual(len(self.handler_periodical.buffer), 2, "Buffer size should be 2")

        time.sleep(2.5)  # wait a bit so the periodical timer thread has kicked off the buffer flush

        document = self.handler_periodical.collection.find_one({'message': 'test periodical buffer'})
        self.assertIsNotNone(document, "Should not have been written to database")
        doc_amount = self.handler_periodical.collection.find({'message': 'test periodical buffer'}).count()
        self.assertEqual(doc_amount, 2, "Should have found 2 documents written to database")
        self.assertEqual(len(self.handler_periodical.buffer), 0, "Buffer should be empty")

        self.assertTrue(self.handler_periodical.buffer_timer_thread.is_alive())
        self.handler_periodical.destroy()
        time.sleep(0.2)  # waiting a tiny bit so that the child thread actually exits
        self.assertFalse(self.handler_periodical.buffer_timer_thread.is_alive(),
                         "Child timer thread should be dead by now. Slow computer?")

        # reset to previous
        self.log.removeHandler(self.handler_periodical)
        self.log.addHandler(self.handler)
