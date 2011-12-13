import unittest
from log4mongo.test import test_mongo_handler

if __name__ == "__main__":
    loader = unittest.TestLoader()
    suite  = unittest.TestSuite()
    suite.addTests(loader.loadTestsFromModule(test_mongo_handler))
    unittest.TextTestRunner(verbosity=2).run(suite)