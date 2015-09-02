import types
from unittest import TestCase
import urllib2
from couchdb.client import Database
from django.contrib.auth.models import User
from django.http import HttpRequest
import jsonpickle
from mock import Mock, patch, MagicMock
from mangrove.errors.MangroveException import FormModelDoesNotExistsException
from mangrove.datastore.database import DatabaseManager

http_basic_patch = patch('datawinners.common.authorization.httpbasic', lambda x: x)
http_basic_patch.start()
datasender_patch = patch('datawinners.common.authorization.is_not_datasender', lambda x: x)
datasender_patch.start()
from datawinners.feeds.views import feed_entries, stream_feeds


class TestFeedView(TestCase):
    def test_error_when_form_code_is_not_present(self):
        request = HttpRequest()
        request.GET['start_date'] = urllib2.quote("21-12-2001 12:12:57".encode("utf-8"))
        request.GET['end_date'] = urllib2.quote("21-12-2002 12:12:57".encode("utf-8"))
        request.user = 'someuser'

        with patch('datawinners.feeds.views.get_form_model_by_code') as get_form_model_by_code:
            with patch('datawinners.feeds.views.get_database_manager') as get_db_manager:
                get_db_manager.return_value = Mock(spec=DatabaseManager)
                get_form_model_by_code.side_effect = FormModelDoesNotExistsException(None)
                response = feed_entries(request, None)
                self.assertEqual(400, response.status_code)
                response_content = jsonpickle.decode(response.content)
                self.assertEquals(response_content.get('ERROR_CODE'), 101)
                self.assertEquals(response_content.get('ERROR_MESSAGE'), 'Invalid form code provided')

    def test_error_when_form_code_is_empty(self):
        request = HttpRequest()
        request.GET['start_date'] = urllib2.quote("21-12-2001 12:12:57".encode("utf-8"))
        request.GET['end_date'] = urllib2.quote("21-12-2002 12:12:57".encode("utf-8"))
        request.user = 'someuser'
        with patch('datawinners.feeds.views.get_form_model_by_code') as get_form_model_by_code:
            with patch('datawinners.feeds.views.get_database_manager') as get_db_manager:
                get_db_manager.return_value = Mock(spec=DatabaseManager)
                get_form_model_by_code.side_effect = FormModelDoesNotExistsException('  ')
                response = feed_entries(request, "     ")
                self.assertEqual(400, response.status_code)
                response_content = jsonpickle.decode(response.content)
                self.assertEquals(response_content.get('ERROR_CODE'), 101)
                self.assertEquals(response_content.get('ERROR_MESSAGE'), 'Invalid form code provided')


    def test_error_when_form_code_invalid(self):
        request = HttpRequest()
        request.GET['start_date'] = urllib2.quote("21-12-2001 12:12:57".encode("utf-8"))
        request.GET['end_date'] = urllib2.quote("21-12-2002 12:12:57".encode("utf-8"))
        request.user = 'someuser'
        with patch('datawinners.feeds.views.get_form_model_by_code') as get_form_model_by_code:
            with patch('datawinners.feeds.views.get_database_manager') as get_db_manager:
                get_db_manager.return_value = Mock(spec=DatabaseManager)
                get_form_model_by_code.side_effect = FormModelDoesNotExistsException('non-existent-form-code')
                response = feed_entries(request, "non-existent-form-code")
                self.assertEqual(400, response.status_code)
                response_content = jsonpickle.decode(response.content)
                self.assertEquals(response_content.get('ERROR_CODE'), 101)
                self.assertEquals(response_content.get('ERROR_MESSAGE'), 'Invalid form code provided')


    def test_error_when_start_date_not_provided(self):
        request = HttpRequest()
        user = MagicMock(spec=User)
        request.user = user
        response = feed_entries(request, "cli001")
        self.assertEqual(400, response.status_code)
        response_content = jsonpickle.decode(response.content)
        self.assertEquals(response_content.get('ERROR_CODE'), 102)
        self.assertEquals(response_content.get('ERROR_MESSAGE'), 'Invalid Start Date provided')


    def test_error_when_start_date_is_empty(self):
        request = HttpRequest()
        user = MagicMock(spec=User)
        request.user = user
        request.GET['start_date'] = "     "

        response = feed_entries(request, "cli001")
        self.assertEqual(400, response.status_code)
        response_content = jsonpickle.decode(response.content)
        self.assertEquals(response_content.get('ERROR_CODE'), 102)
        self.assertEquals(response_content.get('ERROR_MESSAGE'), 'Invalid Start Date provided')


    def test_error_when_start_date_is_not_in_correct_format(self):
        request = HttpRequest()
        user = MagicMock(spec=User)
        request.user = user
        request.GET['start_date'] = urllib2.quote("21/12/2001".encode("utf-8"))
        response = feed_entries(request, "cli001")
        self.assertEqual(400, response.status_code)
        response_content = jsonpickle.decode(response.content)
        self.assertEquals(response_content.get('ERROR_CODE'), 102)
        self.assertEquals(response_content.get('ERROR_MESSAGE'), 'Invalid Start Date provided')

    def test_error_when_end_date_not_provided(self):
        request = HttpRequest()
        user = MagicMock(spec=User)
        request.user = user
        request.GET['start_date'] = urllib2.quote("21-12-2001 12:12:57".encode("utf-8"))
        response = feed_entries(request, "cli001")
        self.assertEqual(400, response.status_code)
        response_content = jsonpickle.decode(response.content)
        self.assertEquals(response_content.get('ERROR_CODE'), 102)
        self.assertEquals(response_content.get('ERROR_MESSAGE'), 'Invalid End Date provided')


    def test_error_when_end_date_is_empty(self):
        request = HttpRequest()
        user = MagicMock(spec=User)
        request.user = user
        request.GET['start_date'] = urllib2.quote("21-12-2001 12:12:57".encode("utf-8"))
        request.GET['end_date'] = "   "

        response = feed_entries(request, "cli001")
        self.assertEqual(400, response.status_code)
        response_content = jsonpickle.decode(response.content)
        self.assertEquals(response_content.get('ERROR_CODE'), 102)
        self.assertEquals(response_content.get('ERROR_MESSAGE'), 'Invalid End Date provided')


    def test_error_when_end_date_is_not_in_correct_format(self):
        request = HttpRequest()
        user = MagicMock(spec=User)
        request.user = user
        request.GET['start_date'] = urllib2.quote("21-12-2001 12:12:57".encode("utf-8"))
        request.GET['end_date'] = urllib2.quote("21-12-2001".encode("utf-8"))

        response = feed_entries(request, "cli001")
        self.assertEqual(400, response.status_code)
        response_content = jsonpickle.decode(response.content)
        self.assertEquals(response_content.get('ERROR_CODE'), 102)
        self.assertEquals(response_content.get('ERROR_MESSAGE'), 'Invalid End Date provided')

    def test_error_when_end_date_is_less_than_start_date(self):
        request = HttpRequest()
        user = MagicMock(spec=User)
        request.user = user
        request.GET['start_date'] = urllib2.quote("21-12-2001 12:12:57".encode("utf-8"))
        request.GET['end_date'] = urllib2.quote("21-12-2001 12:12:56".encode("utf-8"))

        response = feed_entries(request, "cli001")
        self.assertEqual(400, response.status_code)
        response_content = jsonpickle.decode(response.content)
        self.assertEquals(response_content.get('ERROR_CODE'), 103)
        self.assertEquals(response_content.get('ERROR_MESSAGE'), 'End Date provided is less than Start Date')

    def test_stream_in_feeds(self):
        feed_db = Mock(spec=DatabaseManager)
        feed_db.database = Mock(Database)
        feed_db.database.iterview.return_value = [{'value': {'first': 'first'}}, {'value': {'second': 'second'}}]
        response = stream_feeds(feed_db, '', '')
        expected = '[{"first": "first"},{"second": "second"}]'
        response_str = ''
        for r in list(response):
            response_str += r
        self.assertEquals(response_str, expected)
        self.assertTrue(isinstance(response, types.GeneratorType))


http_basic_patch.stop()
datasender_patch.stop()