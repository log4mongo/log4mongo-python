from setuptools import setup
import log4mongo
import os

# Utility function to read the README file.
# Used for the long_description.  It's nice, because now 1) we have a top level
# README file and 2) it's easier to type in the README file than to put a raw
# string in below ...
def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


setup(
    name='log4mongo',
    version=log4mongo.__version__,
    description='handler for MongoDB database for python logging',
    long_description=read('README'),
    author='Vladimir Gorej',
    author_email='gorej@codescale.net',
    url='http://log4mongo.org/display/PUB/Log4mongo+for+Python',
    license='BSD',
    keywords = "mongodb mongo logging handler",
    install_requires=['pymongo'],
    packages=['log4mongo']
)
