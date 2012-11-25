#!/usr/bin/env python
# vim: fileencoding=utf-8
from setuptools import setup, find_packages

setup(
    name='fakeio',
    version='0.1.0',
    description='Fake builtin function open.',
    author='draftcode',
    author_email='draftcode@gmail.com',
    url='https://github.com/draftcode/fakeio',
    install_requires=['distribute'],
    packages=['fakeio'],
    classifiers=[
        'Development Status :: 4 - Beta',
        'License :: OSI Approved :: MIT License',
        ],
    )

