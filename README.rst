FakeIO: Intercept open
======================

FakeIO is a library for testing functions that will open a file.

.. code:: python

    import fakeio

    fakeio_session = fakeio.FakeIOSession()
    fakeio_session.create_file("/memfile/testfile.txt", 'r', content="test")
    with fakeio_session:
        open("/memfile/testfile.txt", 'r').read() # => "test"

You can find the usages in the tests.

You do not want to open a file in a test. So most of the time, the program is
written to receive a file-like object instead of a file path. This will enable
you to test with in-memory file-like object like the one that StringIO
provides. In spite of that, sometimes you want to pass a file path: when you
write acceptance tests or when you write a program that creates files under
some directory. This library lets you intercept calls to the ``open`` built-in
function and replace its return value with a StringIO object.

This library is not intended to replace StringIO. You should use StringIO as
possible as you can.

Example use case
----------------

Assume that you want to write some tests for the function that creates an
error log only if an error happens, and the error log filename can be
determined only after the error occurs. You can write this function like this:

.. code:: python

    def record_error(target, dirpath):
        try:
            target()
        except Exception as e:
            filepath = os.path.join(dirpath,
                                    gen_filename(e, datetime.datetime.now()))
            with open(filepath, 'w') as f:
                f.write(repr(e))

Things that you want to check about this function are here:

1. The argument ``target`` should be called.
2. If the call to ``target`` does not raise any exception, any file should not
   be created.
3. If the call to ``target`` raise an exception, a file should be created
   under the ``dirpath`` directory.
4. The created file should be created under the name which ``gen_filename``
   returns, and ``gen_filename`` should be called properly.
5. The created file's content should be same as ``repr(e)``.

You can write these tests like this:

.. code:: python

    class TestRecordError(unittest.TestCase):
        def test_target_should_be_called(self):
            mock_target = mock.Mock()
            record_error(mock_target, 'does not exists')
            mock_target.assert_called_with()

        def test_it_should_not_create_a_file(self):
            mock_target = mock.Mock()
            fakeio_session = fakeio.FakeIOSession()
            fakeio_session.intercept_regex(re.compile("^/memfile/"))
            with fakeio_session:
                record_error(mock_target, '/memfile')
            self.assertEqual(len(fakeio_session.mappings), 0)

        def test_it_should_create_a_file_if_an_error_occurs(self):
            mock_target = mock.Mock()
            mock_target.side_effect = Exception("Boom!")
            fakeio_session = fakeio.FakeIOSession()
            fakeio_session.intercept_regex(re.compile("^/memfile/"))
            with fakeio_session:
                record_error(mock_target, '/memfile')
            self.assertEqual(len(fakeio_session.mappings), 1)

        def test_created_filename_is_generated_with_gen_filename(self):
            mock_target = mock.Mock()
            e = Exception("Boom!")
            mock_target.side_effect = e
            fakeio_session = fakeio.FakeIOSession()
            fakeio_session.intercept_regex(re.compile("^/memfile/"))
            with fakeio_session, \
                 mock.patch("__main__.gen_filename") as mock_gen_filename, \
                 mock.patch("datetime.datetime") as mock_datetime:
                 mock_gen_filename.return_value = "GeneratedFileName.txt"
                 record_error(mock_target, '/memfile')
                 mock_gen_filename.assert_called_with(
                    e, mock_datetime.now.return_value)
            self.assertEqual(
                os.path.basename(fakeio_session.mappings.keys()[0]),
                "GeneratedFileName.txt")

        def test_content_is_same_as_repr_of_exception(self):
            mock_target = mock.Mock()
            e = Exception("Boom!")
            mock_target.side_effect = e
            fakeio_session = fakeio.FakeIOSession()
            fakeio_session.intercept_regex(re.compile("^/memfile/"))
            with fakeio_session:
                record_error(mock_target, '/memfile')
            key = fakeio_session.mappings.keys()[0]
            file = fakeio_session.mappings[key]
            self.assertEqual(file.getvalue(), repr(e))

Misuse
------

You should not write a function like this:

.. code:: python

    def write_something(filepath, iter):
        with open(filepath, 'w') as f:
            for value in iter:
                f.write(value)

Instead, you should write this like:

.. code:: python

    def write_something(fobj, iter):
        for value in iter:
            fobj.write(value)

With this design, you can test with StringIO. FakeIO is intended to use with
the function whose role is related to opening files.
