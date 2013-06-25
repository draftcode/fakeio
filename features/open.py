# -*- coding: utf-8 -*-
from __future__ import division, absolute_import, print_function, unicode_literals
from lettuce import step, world
import fakeio

@step(u'Given I make a file with byte string "([^"]*)" encoded with "([^"]*)" and specify no encoding')
def given_i_make_a_file_with_byte_string_group1_encoded_with_group2_and_specify_no_encoding(step, content, encoding):
    world.mock_file = fakeio.FakeIOFile("/somepath", "r", content.encode(encoding), None)

@step(u'When I read its contents through __builtins__.open')
def when_i_read_its_contents_through___builtins___open(step):
    world.read_content = world.mock_file.open("r").read()

@step(u'Then I get a value which is instance of str')
def then_i_get_a_value_which_is_instance_of_str(step):
    assert isinstance(world.read_content, str)

@step(u'And it is encoded in "([^"]*)"')
def and_it_is_encoded_in_group1(step, encoding):
    world.read_content.decode(encoding)

@step(u'Given I make a file with byte string "([^"]*)" encoded with "([^"]*)" and specify "([^"]*)" encoding')
def given_i_make_a_file_with_byte_string_group1_encoded_with_group2_and_specify_group2_encoding(step, content, encoding1, encoding2):
    world.mock_file = fakeio.FakeIOFile("/somepath", "r", content.encode(encoding1), encoding2)

@step(u'Then I get an UnicodeDecodeError when reading its contents through __builtins__.open')
def then_i_get_a_unicodedecodeerror_when_reading_its_contents_through___builtins___open(step):
    try:
        world.mock_file.open("r").read()
        assert False
    except UnicodeDecodeError:
        pass

@step(u'Given I make a file with unicode string "([^"]*)" and specify no encoding')
def given_i_make_a_file_with_unicode_string_group1_and_specify_no_encoding(step, content):
    world.mock_file = fakeio.FakeIOFile("/somepath", "r", content, None)

@step(u'Given I make a file with unicode string "([^"]*)" and specify "([^"]*)" encoding')
def given_i_make_a_file_with_unicode_string_group1_and_specify_group2_encoding(step, content, encoding):
    world.mock_file = fakeio.FakeIOFile("/somepath", "r", content, encoding)

@step(u'When I read its contents through io.open')
def when_i_read_its_contents_through_io_open(step):
    world.read_content = world.mock_file.io_open("r", 'utf8').read()

@step(u'Then I get a value which is instance of unicode')
def then_i_get_a_value_which_is_instance_of_unicode(step):
    assert isinstance(world.read_content, unicode)

@step(u'Then I get an UnicodeDecodeError when reading its contents through io.open')
def then_i_get_an_unicodedecodeerror_when_reading_its_contents_through_io_open(step):
    try:
        world.mock_file.io_open("r", 'utf8').read()
        assert False
    except UnicodeDecodeError:
        pass
