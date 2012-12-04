#!/usr/bin/env python
# vim: fileencoding=utf-8
from __future__ import (unicode_literals, print_function, absolute_import)
import unittest
import fakeio
import re
import __builtin__

class TestFakeIOSession(unittest.TestCase):

    def test_should_map_when_with_statement(self):
        fakeio_session = fakeio.FakeIOSession()
        filepath = "/memfile/something.txt"
        content = "something"

        fakeio_session.create_file(filepath, 'r', content)
        with self.assertRaises(IOError):
            open(filepath, 'r')
        with fakeio_session:
            self.assertEqual(open(filepath, 'r').read(), content)

    def test_should_unmap_when_exit_with_statement(self):
        fakeio_session = fakeio.FakeIOSession()
        filepath = "/memfile/something.txt"
        content = "something"

        fakeio_session.create_file(filepath, 'r', content)
        with fakeio_session:
            pass
        with self.assertRaises(IOError):
            open(filepath, 'r')

    def test_should_raise_IOError_when_no_such_file_exists(self):
        fakeio_session = fakeio.FakeIOSession()

        with self.assertRaises(IOError), fakeio_session:
            open("/memfile/notfound.txt", 'r')

    def test_should_pass_through_normal_file(self):
        fakeio_session = fakeio.FakeIOSession()
        content = open(__file__, 'r').read()

        with fakeio_session:
            self.assertEqual(open(__file__, 'r').read(), content)

    def test_should_mapped_string_has_name(self):
        fakeio_session = fakeio.FakeIOSession()
        filepath = "/memfile/something.txt"

        fakeio_session.create_file(filepath, 'r', 'content')
        with fakeio_session:
            fileobj = open(filepath, 'r')
            self.assertEqual(fileobj.name, filepath)

    def test_should_be_able_to_open_again_after_closed(self):
        fakeio_session = fakeio.FakeIOSession()
        filepath = "/memfile/something.txt"

        fakeio_session.create_file(filepath, 'r', 'content')
        with fakeio_session:
            fileobj = open(filepath, 'r')
            fileobj.read()
            fileobj.close()
            fileobj = open(filepath, 'r')
            fileobj.read()
            fileobj.close()

    def test_should_create_writable_file(self):
        fakeio_session = fakeio.FakeIOSession()
        filepath = "/memfile/writable.txt"
        content = 'something'

        writable_fileobj = fakeio_session.create_file(filepath, 'rw')
        with fakeio_session:
            fileobj = open(filepath, 'w')
            fileobj.write(content)
            fileobj.close()
        self.assertEqual(writable_fileobj.getvalue(), content)

    def test_should_be_able_to_open_again_after_closed_wriable(self):
        fakeio_session = fakeio.FakeIOSession()
        filepath = "/memfile/writable.txt"
        content = 'something'

        writable_fileobj = fakeio_session.create_file(filepath, 'rw')
        with fakeio_session:
            fileobj = open(filepath, 'w')
            fileobj.write(content)
            fileobj.close()

            fileobj = open(filepath, 'r')
            self.assertEqual(fileobj.read(), content)

    def test_should_intercept_regex(self):
        fakeio_session = fakeio.FakeIOSession()

        fakeio_session.intercept_regex(re.compile("^/memfile/"))
        with fakeio_session:
            fileobj = open("/memfile/something.txt", 'w')
            fileobj.write('something')

    def test_should_return_faked_file_mappings(self):
        fakeio_session = fakeio.FakeIOSession()
        filepath_regex = "/memfile/something_regex.txt"
        filepath_mapping = "/memfile/something_mapping.txt"

        readable_fileobj = fakeio_session.create_file(filepath_mapping, 'r')
        fakeio_session.intercept_regex(re.compile("^/memfile/"))
        with fakeio_session:
            open(filepath_regex, 'w')

        mappings = fakeio_session.mappings
        self.assertIn(filepath_regex, mappings)
        self.assertIn(filepath_mapping, mappings)
        self.assertIs(mappings[filepath_mapping], readable_fileobj)

    def test_should_mapping_have_precedence_over_regex(self):
        fakeio_session = fakeio.FakeIOSession()
        filepath = "/memfile/something.txt"
        regex = "^/memfile/"
        content = "something"

        fakeio_session.create_file(filepath, 'r', content)
        with fakeio_session:
            fileobj = open(filepath, 'r')
            self.assertEqual(fileobj.read(), content)

    def test_should_be_able_to_open_binary_mode(self):
        fakeio_session = fakeio.FakeIOSession()
        filepath = "/memfile/writable.txt"
        content = 'something'

        writable_fileobj = fakeio_session.create_file(filepath, 'rw')
        with fakeio_session:
            fileobj = open(filepath, 'wb')
            fileobj.write(content)
            fileobj.close()
        self.assertEqual(writable_fileobj.getvalue(), content)

    def test_should_match_filepath_with_normalized_form(self):
        fakeio_session = fakeio.FakeIOSession()
        content = "something"

        fakeio_session.create_file("/memfile\\something.txt", 'r', content)
        with fakeio_session:
            # Assert not raise IOError
            open("/memfile/something.txt", 'r')

    def test_should_normalize_filepath_when_open(self):
        fakeio_session = fakeio.FakeIOSession()
        content = "something"

        fakeio_session.create_file("/memfile/something.txt", 'r', content)
        with fakeio_session:
            # Assert not raise IOError
            open("/memfile\\something.txt", 'r')

    def test_should_not_normalized_not_matched_path(self):
        filepath = "/memfile\\something.txt"
        class OpenMock(object):
            def __init__(self):
                self.called = None

            def __call__(self, f, m, b):
                self.called = f
        open_mock = OpenMock()
        saved_open = __builtin__.open
        try:
            __builtin__.open = open_mock

            filepath = "/memfile\\something.txt"
            fakeio_session = fakeio.FakeIOSession()
            with fakeio_session:
                open(filepath)
            self.assertEqual(filepath, open_mock.called)
        finally:
            __builtin__.open = saved_open

    def test_should_match_regex_normalized_filepath(self):
        fakeio_session = fakeio.FakeIOSession()

        fakeio_session.intercept_regex(re.compile("^/memfile/"))
        with fakeio_session:
            # Assert not raise IOError
            open("/memfile\\something.txt", 'w')

class TestFakeIOFile(unittest.TestCase):

    def test_should_getvalue(self):
        content = "something"
        file = fakeio.FakeIOFile("/memfile/something.txt", "rw", content)
        self.assertEqual(file.getvalue(), content)

    def test_should_not_getvalue_if_file_opened(self):
        file = fakeio.FakeIOFile("/memfile/something.txt", "rw", '')
        file.open('r')
        with self.assertRaises(IOError):
            file.getvalue()

    def test_should_open_with_mode_r(self):
        content = "something"
        file = fakeio.FakeIOFile("/memfile/something.txt", "rw", content)
        fileobj = file.open("r")
        self.assertEqual(fileobj.read(), content)

    def test_should_open_with_mode_w(self):
        content = "something"
        file = fakeio.FakeIOFile("/memfile/something.txt", "rw", '')
        fileobj = file.open("w")
        fileobj.write(content)
        fileobj.close()
        self.assertEqual(file.getvalue(), content)

    def test_should_open_only_one(self):
        file = fakeio.FakeIOFile("/memfile/something.txt", "rw", '')
        file.open('r')
        with self.assertRaises(IOError):
            file.open('r')

    def test_should_open_twice(self):
        file = fakeio.FakeIOFile("/memfile/something.txt", "rw", '')
        fileobj = file.open('r')
        fileobj.close()
        file.open('w')

    def test_should_open_with_mode_a(self):
        file = fakeio.FakeIOFile("/memfile/something.txt", "rw", 'some')
        fileobj = file.open('a')
        fileobj.write('thing')
        fileobj.close()
        self.assertEqual(file.getvalue(), 'something')

    def test_should_not_open_readonly_file_with_mode_w(self):
        file = fakeio.FakeIOFile("/memfile/something.txt", "r", '')
        with self.assertRaises(ValueError):
            file.open('w')

    def test_shoul_close_when_exit(self):
        file = fakeio.FakeIOFile("/memfile/something.txt", "rw", '')
        fileobj = file.open('r')
        with fileobj as fileobj:
            pass
        self.assertTrue(fileobj.closed)

class TestNormalizePath(unittest.TestCase):
    def test_should_normalize_windows_path(self):
        normalized = fakeio._normalize_path("C:\\somepath\\something.txt")
        self.assertEqual(normalized, "C:/somepath/something.txt")

    def test_should_normalize_unix_path(self):
        normalized = fakeio._normalize_path("/somepath/something.txt")
        self.assertEqual(normalized, "/somepath/something.txt")

    def test_should_normalize_mixture(self):
        normalized = fakeio._normalize_path("C:\\somepath/something.txt")
        self.assertEqual(normalized, "C:/somepath/something.txt")

if __name__ == '__main__':
    unittest.main()

