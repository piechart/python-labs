import requests
import unittest

class TestWSGIServer(unittest.TestCase):
    host = "http://127.0.0.1"
    port = 9001
    
    
    
    
loader = unittest.TestLoader()
suite = unittest.TestSuite()
a = loader.loadTestsFromTestCase(TestWSGIServer)
suite.addTest(a)

class NewResult(unittest.TextTestResult):
    def getDescription(self, test):
        doc_first_line = test.shortDescription()
        return doc_first_line or ""

class NewRunner(unittest.TextTestRunner):
    resultclass = NewResult

runner = NewRunner(verbosity=2)
runner.run(suite)