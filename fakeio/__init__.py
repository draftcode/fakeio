from __future__ import (unicode_literals, print_function, absolute_import)
__all__ = [
    'FakeIOSession', 'ProgrammingException',
    ]

import __builtin__
import logging
import StringIO
import os

LOGGER = logging.getLogger(__name__)

_FILE_ATTRS = ['__iter__', 'close', 'flush', 'isatty', 'len', 'next', 'pos',
               'read', 'readline', 'readlines', 'seek', 'tell', 'truncate',
               'write', 'writelines']

class ProgrammingException(Exception):
    pass

class ReadOpenedFakeIOFile(object):
    def __init__(self, filepath, content, file):
        self._filepath = filepath
        self._content = StringIO.StringIO(content)
        self._file = file
        for attr in _FILE_ATTRS:
            if not hasattr(self, attr):
                setattr(self, attr, getattr(self._content, attr))

    @property
    def name(self):
        return self._filepath

    @property
    def closed(self):
        return self._content.closed

    @property
    def softspace(self):
        return self._content.softspace

    def close(self):
        self._file._close(self)
        self._content.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

class WriteOpenedFakeIOFile(object):
    def __init__(self, filepath, content, file):
        self._filepath = filepath
        self._content = StringIO.StringIO()
        self._content.write(content)
        self._content.seek(0)
        self._file = file
        for attr in _FILE_ATTRS:
            if not hasattr(self, attr):
                setattr(self, attr, getattr(self._content, attr))

    @property
    def name(self):
        return self._filepath

    @property
    def closed(self):
        return self._content.closed

    @property
    def softspace(self):
        return self._content.softspace

    def close(self):
        self._file._close(self)
        self._file._sync_content(self._content.getvalue())
        self._content.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

class FakeIOFile(object):
    def __init__(self, filepath, mode, content):
        self._filepath = filepath
        self._mode = mode
        self._content = content
        self._open_file = None

    def open(self, mode):
        if mode.startswith('r'):
            if self._open_file != None:
                raise IOError("File can be simultaneously opened by only one")
            self._open_file = ReadOpenedFakeIOFile(self._filepath,
                                                   self._content, self)
            return self._open_file
        elif mode.startswith('w') or mode.startswith('a'):
            if self._open_file != None:
                raise IOError("File can be simultaneously opened by only one")
            if self._mode != 'rw':
                raise ValueError("File open mode is not consistent")
            self._open_file = WriteOpenedFakeIOFile(self._filepath,
                                                    self._content, self)
            if mode.startswith('a'):
                self._open_file.seek(0, os.SEEK_END)
            return self._open_file
        else:
            raise ValueError("File open mode cannot be parsed")

    def _sync_content(self, content):
        self._content = content

    def _close(self, open_file):
        if self._open_file == open_file:
            self._open_file = None
            return
        raise ProgrammingException('File is not opened but closed.')

    def getvalue(self):
        if self._open_file != None:
            raise IOError("File is still opened")
        return self._content

class FakeIOSession(object):
    def __init__(self):
        self._saved_open = None
        self._mappings = dict()
        self._regexes = []

    def intercept_regex(self, regex):
        self._regexes.append(regex)

    def create_file(self, filepath, mode='r', content=None):
        filepath = _normalize_path(filepath)
        fileobj = FakeIOFile(filepath, mode, content)
        self._mappings[filepath] = fileobj
        return fileobj

    @property
    def mappings(self):
        return self._mappings.copy()

    def _fake_open(self, filepath, mode='r', buffering=-1):
        LOGGER.info("Open file %s in mode %s with buffering %d" %
                    (filepath, mode, buffering))
        normalized_path = _normalize_path(filepath)
        if normalized_path in self._mappings:
            return self._mappings[normalized_path].open(mode)
        for regex in self._regexes:
            if regex.match(normalized_path):
                self.create_file(normalized_path, 'rw')
                return self._mappings[normalized_path].open(mode)
        return self._saved_open(filepath, mode, buffering)

    def __enter__(self):
        LOGGER.info("Fake __builtin__.open")

        self._saved_open = __builtin__.open
        __builtin__.open = self._fake_open

    def __exit__(self, exc_type, exc_value, traceback):
        LOGGER.info("Restore __builtin__.open")

        __builtin__.open = self._saved_open
        self._saved_open = None

def _normalize_path(path):
    return path.replace("\\", "/")
