from __future__ import (unicode_literals, print_function, absolute_import)
__all__ = ['FakeIOSession']

import __builtin__
import logging
import StringIO
import os
import io

LOGGER = logging.getLogger(__name__)

_FILE_ATTRS = ['__iter__', 'close', 'flush', 'isatty', 'len', 'next', 'pos',
               'read', 'readline', 'readlines', 'seek', 'tell', 'truncate',
               'write', 'writelines']

class ProgrammingException(Exception):
    pass

class FakeTextIOFile(object):

    def __init__(self, filepath, content, file):
        self._filepath = filepath
        self._content = io.StringIO(content)
        self._file = file

    # FileIO

    @property
    def mode(self):
        pass

    @property
    def name(self):
        return self._filepath

    # TextIOBase

    @property
    def encoding(self):
        pass

    @property
    def errors(self):
        pass

    @property
    def newlines(self):
        pass

    def detach(self):
        return self._content.detach()

    def read(self, n=-1):
        return self._content.read(n)

    def readline(self):
        return self._content.readline()

    def write(self, s):
        return self._content.write(s)

    # IOBase

    def close(self):
        self._file._close(self)
        self._file._sync_content(self._content.getvalue())
        self._content.close()

    @property
    def closed(self):
        return self._content.closed

    def fileno(self):
        return self._content.fileno()

    def flush(self):
        return self._content.flush()

    def isatty(self):
        return self._content.isatty()

    def readable(self):
        return self._content.readable()

    def readline(self, limit=-1):
        return self._content.readline(limit)

    def readlines(self, hint=-1):
        return self._content.readlines(hint)

    def seek(self, offset, whence=io.SEEK_SET):
        return self._content.seek(offset, whence)

    def seekable(self):
        return self._content.seekable()

    def truncate(self, size=None):
        return self._content.truncate(size)

    def writable(self):
        return self._content.writable()

    def writelines(self, lines):
        return self._content.writelines(lines)

class ReadOpenedFakeIOFile(object):
    def __init__(self, filepath, content, file):
        self._filepath = filepath
        self._content = StringIO.StringIO(content)
        self._file = file
        for attr in _FILE_ATTRS:
            if not hasattr(self, attr):
                setattr(self, attr, getattr(self._content, attr))

    def __iter__(self):
        return self._content.__iter__()

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

    def __iter__(self):
        return self._content.__iter__()

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
    def __init__(self, filepath, mode, content, encoding=None):
        self._filepath = filepath
        self._mode = mode
        self._content = content
        self._encoding = encoding
        self._open_file = None

    def open(self, mode):
        if isinstance(self._content, unicode):
            if self._encoding:
                content = self._content.encode(self._encoding)
            else:
                content = self._content.encode('utf8')
        elif isinstance(self._content, str):
            if self._encoding:
                # Check the encoding is valid
                self._content.decode(self._encoding)
            content = self._content
        elif self._content is None:
            content = ''

        if mode.startswith('r'):
            if self._open_file != None:
                raise IOError("File can be simultaneously opened by only one")
            self._open_file = ReadOpenedFakeIOFile(self._filepath,
                                                   content, self)
            return self._open_file
        elif mode.startswith('w') or mode.startswith('a'):
            if self._open_file != None:
                raise IOError("File can be simultaneously opened by only one")
            if self._mode != 'rw':
                raise ValueError("File open mode is not consistent")
            self._open_file = WriteOpenedFakeIOFile(self._filepath,
                                                    content, self)
            if mode.startswith('a'):
                self._open_file.seek(0, os.SEEK_END)
            return self._open_file
        else:
            raise ValueError("File open mode cannot be parsed")

    def io_open(self, mode, encoding):
        if isinstance(self._content, unicode):
            content = self._content
        elif isinstance(self._content, str):
            if self._encoding:
                content = self._content.decode(self._encoding)
            else:
                content = unicode(self._content)
        elif self._content is None:
            content = ''

        if self._open_file != None:
            raise IOError("File can be simultaneously opened by only one")
        self._open_file = FakeTextIOFile(self._filepath, content, self)
        return self._open_file

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

    def _fake_io_open(self, filepath, mode='r', buffering=-1, encoding=None,
                      errors=None, newline=None, closefd=True):
        LOGGER.info("Open file %s in mode %s with buffering %d, encoding %s "
                    "errors %s, newline %s and closefd %s" %
                    (filepath, mode, buffering, encoding, errors, newline,
                     closefd))
        normalized_path = _normalize_path(filepath)
        if normalized_path in self._mappings:
            return self._mappings[normalized_path].io_open(mode, encoding)
        for regex in self._regexes:
            if regex.match(normalized_path):
                self.create_file(normalized_path, 'rw')
                return self._mappings[normalized_path].io_open(mode, encoding)
        return self._saved_io_open(filepath, mode, buffering, encoding,
                                   errors, newline, closefd)

    def __enter__(self):
        LOGGER.info("Fake __builtin__.open")

        self._saved_open = __builtin__.open
        self._saved_io_open = io.open
        __builtin__.open = self._fake_open
        io.open = self._fake_io_open

    def __exit__(self, exc_type, exc_value, traceback):
        LOGGER.info("Restore __builtin__.open")

        io.open = self._saved_io_open
        __builtin__.open = self._saved_open
        self._saved_io_open = None
        self._saved_open = None

def _normalize_path(path):
    return path.replace("\\", "/")
