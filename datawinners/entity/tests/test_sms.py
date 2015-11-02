from unittest import TestCase

from elasticsearch_dsl.utils import AttrList
from mock import MagicMock, patch
from mangrove.datastore.database import DatabaseManager

from datawinners.entity.view.send_sms import SendSMS, _get_all_contacts_details, \
    _get_all_contacts_details_with_mobile_number
from datawinners.search.tests.test_entity_search import SimpleResult


class TestSMS(TestCase):
    def test_should_return_unique_mobile_numbers(self):
        mock_request = MagicMock()
        mock_request.POST = {"others": "87687687,9879879, 9879879", "recipient": "others"}

        actual_numbers = SendSMS()._other_numbers(mock_request)
        expected_numbers = list(set(["87687687", "9879879"]))
        self.assertListEqual(actual_numbers, expected_numbers)

    def test_should_fetch_mobile_numbers_for_given_questionnaire_names_when_recipient_is_linked(self):
        dbm = MagicMock(spec=DatabaseManager)
        request = MagicMock()
        request.POST = {'recipient': "linked", 'questionnaire-names': '["questionnaire1", "questionnaire2"]'}

        with patch(
                "datawinners.entity.view.send_sms.SendSMS._mobile_numbers_for_questionnaire") as mock_mobile_numbers_for_questionnaire:
            mock_mobile_numbers_for_questionnaire.return_value = ["72465823", "4837539"]

            mobile_numbers = SendSMS()._get_mobile_numbers_for_registered_data_senders(dbm, request)

            mock_mobile_numbers_for_questionnaire.assert_called_once_with(dbm, ["questionnaire1", "questionnaire2"])

            self.assertListEqual(mobile_numbers, ["72465823", "4837539"])

    def test_should_fetch_no_mobile_numbers_when_recipient_is_others(self):
        dbm = MagicMock(spec=DatabaseManager)
        request = MagicMock()
        request.POST = {'recipient': "others"}

        mobile_numbers = SendSMS()._get_mobile_numbers_for_registered_data_senders(dbm, request)

        self.assertListEqual(mobile_numbers, [])

    def test_should_return_contact_mobile_numbers_along_with_name_and_reporter_id(self):
        dbm = MagicMock(spec=DatabaseManager)
        search_parameters = MagicMock()

        with patch(
                "datawinners.entity.view.send_sms.get_all_datasenders_search_results") as get_all_datasenders_search_results_mock:
            result_mock = MagicMock()
            result1 = SimpleResult()
            result1.name = ['ds1']
            result1.short_code = ['code1']
            result1.mobile_number = ['123456']

            result2 = SimpleResult()
            result2.name = ['ds2']
            result2.short_code = ['code2']
            result2.mobile_number = ['98765']

            result_mock.hits = AttrList([result1, result2])
            get_all_datasenders_search_results_mock.return_value = result_mock

            actual_mobile_numbers, actual_contact_display_list = _get_all_contacts_details(dbm, search_parameters)

            self.assertListEqual(actual_mobile_numbers, ['123456', '98765'])
            self.assertListEqual(actual_contact_display_list, ['ds1 (code1)', 'ds2 (code2)'])

    def test_should_return_contact_mobile_numbers_along_with_mobile_number_and_reporter_id_when_no_name_present(self):
        dbm = MagicMock(spec=DatabaseManager)
        search_parameters = MagicMock()

        with patch(
                "datawinners.entity.view.send_sms.get_all_datasenders_search_results") as get_all_datasenders_search_results_mock:
            result_mock = MagicMock()
            result1 = SimpleResult()
            result1.name = ['ds1']
            result1.short_code = ['code1']
            result1.mobile_number = ['123456']

            result2 = SimpleResult()
            result2.short_code = ['code2']
            result2.mobile_number = ['98765']

            result_mock.hits = AttrList([result1, result2])
            get_all_datasenders_search_results_mock.return_value = result_mock

            actual_mobile_numbers, actual_contact_display_list = _get_all_contacts_details(dbm, search_parameters)

            self.assertListEqual(actual_mobile_numbers, ['123456', '98765'])
            self.assertListEqual(actual_contact_display_list, ['ds1 (code1)', '98765 (code2)'])

    def test_should_return_contact_details_with_mobile_number_search_results_excluding_failed_numbers(self):
        dbm = MagicMock(spec=DatabaseManager)
        search_parameters = MagicMock()
        failed_numbers = ['some_number']
        with patch(
                "datawinners.entity.view.send_sms.get_all_datasenders_search_results") as get_all_datasenders_search_results_mock:
            result_mock = MagicMock()
            result1 = SimpleResult()
            result1.name = ['ds1']
            result1.short_code = ['code1']
            result1.mobile_number = ['some_number']

            result2 = SimpleResult()
            result2.short_code = ['code2']
            result2.mobile_number = ['98765']

            result_mock.hits = AttrList([result1, result2])
            get_all_datasenders_search_results_mock.return_value = result_mock

            actual_mobile_numbers, actual_contact_display_list, actual_short_codes = _get_all_contacts_details_with_mobile_number(
                dbm, search_parameters, failed_numbers)

            self.assertListEqual(actual_mobile_numbers, ['98765'])
            self.assertListEqual(actual_contact_display_list, ['98765 (code2)'])
            self.assertListEqual(actual_short_codes, ['code2'])
