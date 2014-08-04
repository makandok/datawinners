import os
import unittest
from mock import patch
from datawinners.blue.xform_bridge import XlsFormParser, UppercaseNamesNotSupportedException, \
    NestedRepeatsNotSupportedException, MultipleLanguagesNotSupportedException, get_generated_xform_id_name, LanguageNotSameException, \
    LabelForChoiceNotPresentException

DIR = os.path.dirname(__file__)

class TestXformBridge(unittest.TestCase):
    def test_xform_validation_for_uppercase_names(self):
        with patch('datawinners.blue.xform_bridge.parse_file_to_json') as get_xform_dict:
            xls_form_parser = XlsFormParser('some_path', 'questionnaire_name')
            fields = {
                'children': [{u'bind': {u'required': u'yes'}, u'type': u'text', u'name': u'name', u'label': u'Name'}, {
                    u'children': [
                        {u'bind': {u'required': u'no'}, u'type': u'text', u'name': u'college',
                         u'label': u'College Name'}
                    ],
                    # here is uppercase name
                    u'type': u'repeat', u'name': u'Highest_Degree', u'label': u'degree'},
                             {'control': {'bodyless': True}, 'type': 'group', 'name': 'meta', 'children': [
                                 {'bind': {'readonly': 'true()', 'calculate': "concat('uuid:', uuid())"},
                                  'type': 'calculate',
                                  'name': 'instanceID'}]}]}

            get_xform_dict.return_value = fields
            self.assertRaises(UppercaseNamesNotSupportedException, xls_form_parser._validate_fields_are_recognised,
                              fields['children'])

    def test_xform_validation_for_nested_repeats_names(self):
        with patch('datawinners.blue.xform_bridge.parse_file_to_json') as get_xform_dict:
            xls_form_parser = XlsFormParser('some_path', 'questionnaire_name')
            fields = {
                'children': [{u'bind': {u'required': u'yes'}, u'type': u'text', u'name': u'name', u'label': u'Name'},
                             {u'children': [{u'children': [
                                 {u'bind': {u'required': u'no'}, u'type': u'text', u'name': u'college',
                                  u'label': u'College Name'}],
                                             u'type': u'repeat', u'name': u'some', u'label': u'some'}],
                              u'type': u'repeat',
                              u'name': u'Highest_Degree', u'label': u'degree'},
                             {'control': {'bodyless': True}, 'type': 'group', 'name': 'meta', 'children': [
                                 {'bind': {'readonly': 'true()', 'calculate': "concat('uuid:', uuid())"},
                                  'type': 'calculate',
                                  'name': 'instanceID'}]}]}
            get_xform_dict.return_value = fields
            self.assertRaises(NestedRepeatsNotSupportedException, xls_form_parser._validate_fields_are_recognised,
                              fields['children'])


    def test_should_raise_exception_when_label_defined_in_multiple_languages(self):
        with patch('datawinners.blue.xform_bridge.parse_file_to_json') as get_xform_dict:
            xls_form_parser = XlsFormParser('some_path', 'questionnaire_name')
            fields = {'children': [{u'bind': {u'required': u'yes'}, u'type': u'text', u'name': u'name',
                                    u'label': {u'french': u'1. What is your name?',
                                               u'english': u'1. What is your name?'}},
                                   {u'bind': {u'required': u'yes'}, u'type': u'integer', u'name': u'age',
                                    u'label': {u'french': u'2. What is your age?',
                                               u'english': u'2. What is your age?'}},
                                   {u'bind': {u'required': u'yes'}, u'type': u'text', u'name': u'new_loc',
                                    u'label': {u'french': u'1. What is your new loc?',
                                               u'english': u'1. What is your new loc?'}},
                                   {'control': {'bodyless': True}, 'type': 'group', 'name': 'meta', 'children': [
                                       {'bind': {'readonly': 'true()', 'calculate': "concat('uuid:', uuid())"},
                                        'type': 'calculate', 'name': 'instanceID'}]}]}
            get_xform_dict.return_value = fields
            self.assertRaises(MultipleLanguagesNotSupportedException, xls_form_parser._validate_fields_are_recognised,
                              fields['children'])

    def test_should_not_raise_exception_when_label_defined_in_single_explict_language(self):
        with patch('datawinners.blue.xform_bridge.parse_file_to_json') as get_xform_dict:
            xls_form_parser = XlsFormParser('some_path', 'questionnaire_name')
            fields = {'children': [{u'bind': {u'required': u'yes'}, u'type': u'text', u'name': u'name',
                                    u'label': {u'english': u'1. What is your name?'}},
                                   {u'bind': {u'required': u'yes'}, u'type': u'integer', u'name': u'age',
                                    u'label': {u'english': u'2. What is your age?'}},
                                   {u'bind': {u'required': u'yes'}, u'type': u'text', u'name': u'new_loc',
                                    u'label': {u'english': u'1. What is your new loc?'}},
                                   {'control': {'bodyless': True}, 'type': 'group', 'name': 'meta', 'children': [
                                       {'bind': {'readonly': 'true()', 'calculate': "concat('uuid:', uuid())"},
                                        'type': 'calculate', 'name': 'instanceID'}]}]}
            get_xform_dict.return_value = fields
            try:
                xls_form_parser._validate_fields_are_recognised(fields['children'])
            except MultipleLanguagesNotSupportedException:
                self.fail("Should not throw exception")

    def test_should_raise_exception_when_the_label_and_hint_languages_dont_match(self):
        with patch('datawinners.blue.xform_bridge.parse_file_to_json') as get_xform_dict:
            xls_form_parser = XlsFormParser('some_path', 'questionnaire_name')
            fields = {'children': [{u'bind': {u'required': u'yes'}, u'type': u'text', u'name': u'name',
                                    u'label': {u'french': u'1. What is your name?'},u'hint':{u'hindi':u'Hindi hint'}},
                                   {u'bind': {u'required': u'yes'}, u'type': u'integer', u'name': u'age',
                                    u'label': {u'french': u'2. What is your age?'},u'hint':{u'hindi':u'Hindi hint'}},
                                   {u'bind': {u'required': u'yes'}, u'type': u'text', u'name': u'new_loc',
                                    u'label': {u'french': u'1. What is your new loc?'},u'hint':{u'hindi':u'Hindi hint'}},
                                   {'control': {'bodyless': True}, 'type': 'group', 'name': 'meta', 'children': [
                                       {'bind': {'readonly': 'true()', 'calculate': "concat('uuid:', uuid())"},
                                        'type': 'calculate', 'name': 'instanceID'}]}]}
            get_xform_dict.return_value = fields
            self.assertRaises(LanguageNotSameException, xls_form_parser._validate_fields_are_recognised,
                              fields['children'])

    def test_should_not_raise_exception_when_the_label_and_hint_languages_match(self):
        with patch('datawinners.blue.xform_bridge.parse_file_to_json') as get_xform_dict:
            xls_form_parser = XlsFormParser('some_path', 'questionnaire_name')
            fields = {'children': [{u'bind': {u'required': u'yes'}, u'type': u'text', u'name': u'name',
                                    u'label': {u'french': u'1. What is your name?'},u'hint':{u'french':u'French hint'}},
                                   {u'bind': {u'required': u'yes'}, u'type': u'integer', u'name': u'age',
                                    u'label': {u'french': u'2. What is your age?'},u'hint':{u'french':u'French hint'}},
                                   {u'bind': {u'required': u'yes'}, u'type': u'text', u'name': u'new_loc',
                                    u'label': {u'french': u'1. What is your new loc?'},u'hint':{u'french':u'French hint'}},
                                   {'control': {'bodyless': True}, 'type': 'group', 'name': 'meta', 'children': [
                                       {'bind': {'readonly': 'true()', 'calculate': "concat('uuid:', uuid())"},
                                        'type': 'calculate', 'name': 'instanceID'}]}]}
            get_xform_dict.return_value = fields
            try:
                xls_form_parser._validate_fields_are_recognised(fields['children'])
            except LanguageNotSameException:
                self.fail("Should not throw exception")

    def test_should_raise_exception_when_the_label_of_survey_and_choice_sheets_dont_match(self):
        with patch('datawinners.blue.xform_bridge.parse_file_to_json') as get_xform_dict:
            xls_form_parser = XlsFormParser('some_path', 'questionnaire_name')
            fields = {'children': [{u'bind': {u'required': u'yes'}, u'type': u'text', u'name': u'name',
                                    u'label': {u'french': u'1. What is your name?'}},
                                   {u'bind': {u'required': u'yes'}, u'type': u'integer', u'name': u'age',
                                    u'label': {u'french': u'2. What is your age?'}},
                                   {u'bind': {u'required': u'yes'}, u'type': u'select one', u'name': u'is_student',
                                    u'label': {u'french': u'1. Are you a student?'},u'choices':[{u'name': u'yes', u'label': {u'hindi': u'Yes'}}, {u'name': u'no', u'label': {u'hindi': u'No'}}]},
                                   {'control': {'bodyless': True}, 'type': 'group', 'name': 'meta', 'children': [
                                       {'bind': {'readonly': 'true()', 'calculate': "concat('uuid:', uuid())"},
                                        'type': 'calculate', 'name': 'instanceID'}]}]}
            get_xform_dict.return_value = fields
            self.assertRaises(LanguageNotSameException, xls_form_parser._validate_fields_are_recognised,
                              fields['children'])

    def test_should_raise_exception_when_choice_has_no_label(self):
        with patch('datawinners.blue.xform_bridge.parse_file_to_json') as get_xform_dict:
            xls_form_parser = XlsFormParser('some_path', 'questionnaire_name')
            fields = {'children': [{u'bind': {u'required': u'yes'}, u'type': u'select one', u'name': u'is_student',
                                    u'label': {u'french': u'1. Are you a student?'},u'choices':[{u'name': u'yes'}, {u'name': u'no', u'label': {u'hindi': u'No'}}]},
                                   {'control': {'bodyless': True}, 'type': 'group', 'name': 'meta', 'children': [
                                       {'bind': {'readonly': 'true()', 'calculate': "concat('uuid:', uuid())"},
                                        'type': 'calculate', 'name': 'instanceID'}]}]}
            get_xform_dict.return_value = fields
            self.assertRaises(LabelForChoiceNotPresentException, xls_form_parser._create_questions,
                              fields['children'])


    def test_should_not_raise_exception_when_the_label_of_survey_and_choice_sheets_match(self):
        with patch('datawinners.blue.xform_bridge.parse_file_to_json') as get_xform_dict:
            xls_form_parser = XlsFormParser('some_path', 'questionnaire_name')
            fields = {'children': [{u'bind': {u'required': u'yes'}, u'type': u'text', u'name': u'name',
                                    u'label': {u'french': u'1. What is your name?'}},
                                   {u'bind': {u'required': u'yes'}, u'type': u'integer', u'name': u'age',
                                    u'label': {u'french': u'2. What is your age?'}},
                                   {u'bind': {u'required': u'yes'}, u'type': u'select one', u'name': u'is_student',
                                    u'label': {u'french': u'1. Are you a student?'},u'choices':[{u'name': u'yes', u'label': {u'french': u'Yes'}}, {u'name': u'no', u'label': {u'french': u'No'}}]},
                                   {'control': {'bodyless': True}, 'type': 'group', 'name': 'meta', 'children': [
                                       {'bind': {'readonly': 'true()', 'calculate': "concat('uuid:', uuid())"},
                                        'type': 'calculate', 'name': 'instanceID'}]}]}
            get_xform_dict.return_value = fields
            try:
                xls_form_parser._validate_fields_are_recognised(fields['children'])
            except LanguageNotSameException:
                self.fail("Should not throw exception")

    def test_should_raise_exception_when_the_label_and_constraint_message_languages_dont_match(self):
        with patch('datawinners.blue.xform_bridge.parse_file_to_json') as get_xform_dict:
            xls_form_parser = XlsFormParser('some_path', 'questionnaire_name')
            fields = {'children': [{u'bind': {u'required': u'yes'}, u'type': u'text', u'name': u'name',
                                    u'label': {u'french': u'1. What is your name?'}},
                                   {u'bind': {u'required': u'yes'}, u'type': u'integer', u'name': u'age',
                                    u'label': {u'french': u'2. What is your age?'},u'constraint_message':{u'hindi':u'Hindi constraint message'}},
                                   {u'bind': {u'required': u'yes'}, u'type': u'text', u'name': u'new_loc',
                                    u'label': {u'french': u'1. What is your new loc?'},},
                                   {'control': {'bodyless': True}, 'type': 'group', 'name': 'meta', 'children': [
                                       {'bind': {'readonly': 'true()', 'calculate': "concat('uuid:', uuid())"},
                                        'type': 'calculate', 'name': 'instanceID'}]}]}
            get_xform_dict.return_value = fields
            self.assertRaises(LanguageNotSameException, xls_form_parser._validate_fields_are_recognised,
                              fields['children'])

    def test_should_not_raise_exception_when_the_label_and_constraint_message_languages_match(self):
        with patch('datawinners.blue.xform_bridge.parse_file_to_json') as get_xform_dict:
            xls_form_parser = XlsFormParser('some_path', 'questionnaire_name')
            fields = {'children': [{u'bind': {u'required': u'yes'}, u'type': u'text', u'name': u'name',
                                    u'label': {u'french': u'1. What is your name?'}},
                                   {u'bind': {u'required': u'yes'}, u'type': u'integer', u'name': u'age',
                                    u'label': {u'french': u'2. What is your age?'},u'constraint_message':{u'french':u'French constraint message'}},
                                   {u'bind': {u'required': u'yes'}, u'type': u'text', u'name': u'new_loc',
                                    u'label': {u'french': u'1. What is your new loc?'},},
                                   {'control': {'bodyless': True}, 'type': 'group', 'name': 'meta', 'children': [
                                       {'bind': {'readonly': 'true()', 'calculate': "concat('uuid:', uuid())"},
                                        'type': 'calculate', 'name': 'instanceID'}]}]}
            get_xform_dict.return_value = fields
            try:
                xls_form_parser._validate_fields_are_recognised(fields['children'])
            except LanguageNotSameException:
                self.fail("Should not throw exception")



class TestXformParsing(unittest.TestCase):

    def setUp(self):
         self.test_data = os.path.join(DIR, 'testdata')

    def test_should_return_generated_xform_id_for_questionnaire_with_single_explict_language(self):
        with open (os.path.join(self.test_data, 'xform-single-explict-language.xml'), "r") as file:
            xform_as_string = file.read()
            actual_generated_id = get_generated_xform_id_name(xform_as_string)
            self.assertEqual('tmpl8G0vO', actual_generated_id)