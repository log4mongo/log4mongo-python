# -*- coding: utf-8 -*-
from setuptools import setup
import log4mongo
import os

# Utility function to read the README file.
# Used for the long_description.  It's nice, because now 1) we have a top level
# README file and 2) it's easier to type in the README file than to put a raw
# string in below ...


def read(fname):
    try:
        return open(os.path.join(os.path.dirname(__file__), fname), encoding='utf-8').read()
    except TypeError:  # encoding is only Python3
        return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name='log4mongo',
    version=log4mongo.__version__,
    description='mongo database handler for python logging',
    long_description=read('README.rst'),
    author=u'Vladimír Gorej',
    author_email='gorej@codescale.net',
    url='http://log4mongo.org/display/PUB/Log4mongo+for+Python',
    download_url='http://github.com/log4mongo/log4mongo-python/tarball/master',
    license='BSD',
    keywords = "mongodb mongo logging handler",
    install_requires=['pymongo'],
    packages=['log4mongo', 'log4mongo.test'],
    platforms='any',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Console',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Utilities',
        'Topic :: System :: Logging',
        'Topic :: System :: Monitoring'
    ],
    test_suite='log4mongo.test',
)
