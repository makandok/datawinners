# vim: ai ts=4 sts=4 et sw= encoding=utf-8

from __builtin__ import type
import os
import unittest
from xml.etree import ElementTree as ET
from django.contrib.auth.models import User

from django.test import Client
from mock import Mock, MagicMock
from nose.plugins.attrib import attr

from datawinners.blue.xform_bridge import MangroveService, XlsFormParser, XlsParserResponse
from datawinners.main.database import get_database_manager
from datawinners.project.helper import generate_questionnaire_code
from datawinners.utils import random_string
from mangrove.form_model.field import FieldSet
from mangrove.form_model.form_model import get_form_model_by_code


DIR = os.path.dirname(__file__)

class TestXFormBridge(unittest.TestCase):

    def setUp(self):
        self.test_data = os.path.join(DIR, '../../../datawinners/blue/test/testdata')
        self.UNSUPPORTED_FIELDS = os.path.join(self.test_data, 'unsupported_field.xls')
        self.INVALID_FIELDS = os.path.join(self.test_data,'invalid_field.xls')
        self.CASCADE = os.path.join(self.test_data,'cascade.xls')
        self.ALL_FIELDS = os.path.join(self.test_data,'all_fields.xls')
        self.SIMPLE = os.path.join(self.test_data,'text_and_integer.xls')
        self.REQUIRED = os.path.join(self.test_data,'required_sample.xls')
        self.REPEAT = os.path.join(self.test_data,'repeat.xls')
        self.SKIP = os.path.join(self.test_data,'skip-sample.xls')
        self.MULTI_SELECT = os.path.join(self.test_data,'multi-select.xls')
        self.MANY_FIELD = os.path.join(self.test_data,'many-fields.xls')
        self.NAME_SPACE = os.path.join(self.test_data,'xpath-sample.xml')
        self.user = User.objects.get(username="tester150411@gmail.com")
        self.mock_request = MagicMock()
        self.mock_request.user = self.user


    @attr('functional_test')
    def test_should_throw_error_for_unsupported_valid_field_type(self):
        xls_parser_response = XlsFormParser(self.UNSUPPORTED_FIELDS, u"My questionnairé").parse()
        self.assertEqual(xls_parser_response.errors, set(["geoshape as a datatype"]))

    @attr('functional_test')
    def test_should_throw_error_for_invalid_field_type(self):
        xls_parser_response = XlsFormParser(self.INVALID_FIELDS, u"My questionnairé").parse()
        self.assertEqual(xls_parser_response.errors, set(["dfdfd as a datatype"]))

    @attr('functional_test')
    def test_should_convert_cascaded_select_field(self):
        xls_parser_response  = XlsFormParser(self.CASCADE, "My questionnaire").parse()

        expected_json = [{'code': 'name', 'name': 'What is your name?', 'title': 'What is your name?', 'required': False,
          'is_entity_question': False, 'instruction': 'Answer must be a word', 'parent_field_code': None, 'type': 'text'},
         {'code': 'respondent_district_counties', 'parent_field_code': None, 'title': 'Please select the county', 'required': False,
          'has_other': False,
          'choices': [{'value': {'text': 'Bomi', 'val': 'bomi'}},
                      {'value': {'text': 'Grand Bassa', 'val': 'grand_bassa'}}], 'is_entity_question': False,
          'type': 'select1'},
         {'code': 'respondent_district', 'parent_field_code': None, 'title': 'Please select the district', 'required': False,
          'has_other': False,
          'choices': [{'value': {'text': 'Klay', 'val': 'klay'}},
                      {'value': {'text': 'Commonwealth 1', 'val': 'commonwealth_1'}}], 'is_entity_question': False,
          'type': 'select1'}]

        self.assertEqual(expected_json, xls_parser_response.json_xform_data)

    @attr('functional_test')
    def test_should_create_project_using_xlsform_file(self):
        xls_parser_response = XlsFormParser(self.ALL_FIELDS, u"My questionnairé").parse()

        mangroveService = MangroveService(self.mock_request, xls_parser_response=xls_parser_response)
        quesionnaire_id = mangroveService.create_project()

        self.assertIsNotNone(quesionnaire_id)

    @attr('functional_test')
    def test_should_convert_skip_logic_question(self):
        xls_parser_response = XlsFormParser(self.SKIP, u"My questionnairé").parse()

        mangroveService = MangroveService(self.mock_request, xls_parser_response=xls_parser_response)
        questionnaire_id = mangroveService.create_project()

        self.assertIsNotNone(questionnaire_id)

    @attr('functional_test')
    def test_should_convert_multi_select_question(self):
        xls_parser_response = XlsFormParser(self.MULTI_SELECT, u"My questionnairé").parse()

        mangroveService = MangroveService(self.mock_request, xls_parser_response=xls_parser_response)
        questionnaire_id = mangroveService.create_project()

        self.assertIsNotNone(questionnaire_id)


    @attr('functional_test')
    def test_all_fields_types_in_xlsform_is_converted_to_json(self):

        xls_parser_response = XlsFormParser(self.ALL_FIELDS, "My questionnaire").parse()

        expected_json = \
            [{'code': 'name', 'parent_field_code': None, 'name': 'What is your name?', 'title': 'What is your name?', 'required': True, 'is_entity_question': False, 'instruction': 'Answer must be a word', 'type': 'text'},
                # repeat
             {'code': 'education', 'parent_field_code': None, 'instruction': 'No answer required', 'name': 'Education', 'title': 'Education',
                'fields': [{'code': 'degree', 'parent_field_code': u'education', 'name': 'Degree name', 'title': 'Degree name', 'required': True, 'is_entity_question': False, 'instruction': 'Answer must be a word', 'type': 'text'},
                         {'code': 'completed_on', 'parent_field_code': u'education', 'date_format': 'dd.mm.yyyy', 'name': 'Degree completion year', 'title': 'Degree completion year', 'required': True, 'is_entity_question': False, 'instruction': 'Answer must be a date in the following format: day.month.year. Example: 25.12.2011','event_time_field_flag': False, 'type': 'date'}], 'is_entity_question': False,
                          'type': 'field_set', 'required': False, 'fieldset_type': 'repeat'},
                # end repeat
            {'code': 'age', 'parent_field_code': None, 'name': 'What is your age?', 'title': 'What is your age?', 'required': False, 'is_entity_question': False, 'instruction': 'Answer must be a number', 'type': 'integer'},
             {'code': 'height', 'parent_field_code': None, 'name': 'What is your height?', 'title': 'What is your height?', 'required': False, 'is_entity_question': False, 'instruction': 'Answer must be a decimal or number', 'type': 'integer'},
             {'code': 'fav_color', 'parent_field_code': None, 'title': 'Which colors you like?', 'required': True, 'has_other': False,
                'choices': [{'value':{'text': 'Red', 'val': 'a'}}, {'value': {'text': 'Blue', 'val': 'b'}},
                          {'value':{'text': 'Green', 'val': 'c'}}], 'is_entity_question': False, 'type': 'select'},
                #group
            {'code': u'pizza_test_group', 'parent_field_code': None, 'instruction': 'No answer required', 'name': u'Pizza fan', 'title': u'Pizza fan',
              'fields': [{'code': u'pizza_fan', 'parent_field_code': u'pizza_test_group', 'title': u'Do you like pizza?', 'required': True, 'has_other': False,
                          'choices': [{'value': {'text': u'Yes', 'val': u'a'}}, {'value': {'text': u'No', 'val': u'b'}}],
                          'is_entity_question': False, 'type': 'select1'},
                         #group
                         {'code': u'like_group', 'parent_field_code': u'pizza_test_group', 'instruction': 'No answer required', 'name': u'Like group', 'title': u'Like group',
                          'fields': [
                              {'code': u'other', 'parent_field_code': u'like_group', 'name': u'What else you like?', 'title': u'What else you like?', 'required': False,
                               'is_entity_question': False, 'instruction': 'Answer must be a word', 'type': u'text'},
                              {'code': u'pizza_type', 'parent_field_code': u'like_group', 'name': u'Which pizza type you like?', 'title': u'Which pizza type you like?',
                               'required': False, 'is_entity_question': False, 'instruction': 'Answer must be a word',
                               'type': u'text'}], 'is_entity_question': False, 'type': 'field_set', 'fieldset_type': 'group',
                          'required': False}], 'is_entity_question': False, 'type': 'field_set', 'fieldset_type': 'group', 'required': False},

             {'code': 'location', 'parent_field_code': None, 'name': 'Your location?', 'title': 'Your location?', 'required': False, 'is_entity_question': False, 'instruction': 'Answer must be a geopoint', 'type': 'geocode'},
             {'code': 'add_age_height', 'parent_field_code': None, 'name': 'Age and height', 'title': 'Age and height', 'required': False, 'is_calculated': True, 'is_entity_question': False, 'instruction': 'Answer must be a calculated field', 'type': 'text'},
             {'code': 'ab','parent_field_code': None, 'title': 'A or B?', 'required': True, 'has_other': False,
                'choices': [{'value':{'text': 'A', 'val': 'a'}}, {'value':{'text': 'B', 'val': 'b'}}], 'is_entity_question': False, 'type': 'select1'}]

        self.assertEqual(expected_json, xls_parser_response.json_xform_data)
        self.assertIsNotNone(xls_parser_response.xform_as_string)

    @attr('functional_test')
    def test_sequence_of_the_fields_in_form_model_should_be_same_as_in_xlsform(self):

        xls_parser_response = XlsFormParser(self.MANY_FIELD, "My questionnaire").parse()

        self.assertIsNotNone(xls_parser_response.xform_as_string)
        names = [f['code'] for f in xls_parser_response.json_xform_data]
        expected_names = ["a312name1312","a528name2528","a972name3972","a667name4667","a868name5868","a970name6970","a870name7870","a320name8320","a863name9863","a509name10509","a191name11191","a216name12216","a320name13320","a165name14165","a116name15116","a413name16413","a568name17568","a379name18379","a863name19863","a929name20929","a640name21640","a392name22392","a264name23264","a868name24868","a191name25191","a316name26316","a908name27908","a488name28488","a455name29455","a802name30802","a595name31595","a668name32668","a329name33329","a566name34566","a335name35335","a197name36197","a536name37536","a204name38204","a418name39418","a399name40399","a614name41614","a510name42510","a515name43515","a835name44835","a575name45575","a531name46531","a247name47247","a143name48143","a811name49811","a110name50110"]
        self.assertEqual(names, expected_names)

    def _repeat_codes(self, repeat):
        code = repeat['code']
        children_code = [f['code'] for f in repeat['fields']]
        r = []
        r.append(code)
        r.append(children_code)
        return r

    @attr('functional_test')
    def test_sequence_of_the_mixed_type_fields_in_from_model_should_be_same_as_xlsform(self):
        parser = XlsFormParser(self.REPEAT, "My questionnaire")

        xls_parser_response = parser.parse()

        names = [f['code'] if f['type'] != 'field_set' else self._repeat_codes(f) for f in xls_parser_response.json_xform_data]
        expected_names = ['familyname',
                          ['family',['name','age']],
                          'city',
                          ['house',['name','room','numberofrooms']]]
        self.assertEqual(names, expected_names)

    @attr('functional_test')
    def test_xform_is_the_default_namespace(self):
        # while parsing submission we assume that xform element without namespace since being default.
        xform_as_string = open(self.NAME_SPACE, 'r').read()
        default_namespace_definition_format = 'xmlns="http://www.w3.org/2002/xforms"'

        mangrove_service = MangroveService(self.mock_request, xls_parser_response=XlsParserResponse(xform_as_string=xform_as_string))
        mangrove_service.xform = xform_as_string
        updated_xform = mangrove_service.add_form_code(None)

        self.assertTrue(updated_xform.find(default_namespace_definition_format) != -1)

    def _find_in_instance(self, updated_xform, element_name):
        ET.register_namespace('', 'http://www.w3.org/2002/xforms')
        root = ET.fromstring(updated_xform)
        xform_ns = '{http://www.w3.org/2002/xforms}'
        html_ns = '{http://www.w3.org/1999/xhtml}'
        head_path = '%shead' % html_ns
        path = ['', 'model/', 'instance/', 'summary-project/']
        path.append(element_name)
        element_path = head_path + '/' + xform_ns.join(path)
        element_text = root.findall(element_path)[0].text
        return element_text

    @attr('functional_test')
    def test_should_add_form_code_and_bind_element_to_xform(self):
        xform_as_string = open(self.NAME_SPACE, 'r').read()
        expected_form_code = '022-somthing-making-it-unique-in-xml'

        mangrove_service = MangroveService(self.mock_request, xls_parser_response=XlsParserResponse(xform_as_string=xform_as_string))
        mangrove_service.xform = xform_as_string
        updated_xform = mangrove_service \
            .add_form_code('%s' % expected_form_code)

        form_code = self._find_in_instance(updated_xform, 'form_code')
        self.assertEqual(form_code, expected_form_code)

    @attr('functional_test')
    def test_should_verify_xform_is_stored_when_project_created(self):

        manager = get_database_manager(self.user)
        questionnaire_code = generate_questionnaire_code(manager)
        project_name = 'xform-' + questionnaire_code

        xls_parser_response = XlsFormParser(self.REPEAT, u"My questionnairé").parse()

        mangrove_service = MangroveService(self.mock_request, project_name=project_name, xls_parser_response=xls_parser_response)
        mangrove_service.create_project()

        questionnaire_code = mangrove_service.questionnaire_code
        mgr = mangrove_service.manager
        from_model = get_form_model_by_code(mgr, questionnaire_code)
        self.assertIsNotNone(from_model.xform)

    @attr('functional_test')
    def test_should_verify_repeat_field_added_to_questionnaire(self):
        xls_parser_response = XlsFormParser(self.REPEAT, u"My questionnairé").parse()
        mangroveService = MangroveService(self.mock_request, xls_parser_response=xls_parser_response)
        mangroveService.create_project()

        questionnaire_code = mangroveService.questionnaire_code
        mgr = mangroveService.manager
        from_model = get_form_model_by_code(mgr, questionnaire_code)

        self.assertNotEqual([], [f for f in from_model.fields if type(f) is FieldSet and f.fields])

    @attr('functional_test')
    def test_should_verify_field_is_not_mandatory_when_required_is_not_specified(self):
        xls_parser_response = XlsFormParser(self.REQUIRED, "My questionnaire").parse()

        root = ET.fromstring(xls_parser_response.xform_as_string)
        ET.register_namespace('', 'http://www.w3.org/2002/xforms')

        binds = [node.attrib.get('required') for node in root.iter('{http://www.w3.org/2002/xforms}bind')]

        self.assertEqual('true()', binds[0])
        self.assertEqual(None, binds[1])

