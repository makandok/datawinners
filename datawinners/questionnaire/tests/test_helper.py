import unittest
from mangrove.datastore.database import DatabaseManager
from mangrove.datastore.datadict import DataDictType
from mangrove.form_model.field import HierarchyField, TextField
from mangrove.form_model.form_model import FormModel, LOCATION_TYPE_FIELD_NAME, LOCATION_TYPE_FIELD_CODE
from mock import Mock
from questionnaire.helper import get_location_field_code

class QuestionnaireHelper(unittest.TestCase):

    def test_should_give_location_code(self):
        form_model=self._get_form_model()
        form_model.add_field(self._get_location_field())
        self.assertEqual(LOCATION_TYPE_FIELD_CODE,get_location_field_code(form_model))

    def test_should_return_None_if_location_field_is_not_present(self):
        form_model=self._get_form_model()
        form_model.add_field(self._get_text_field())
        self.assertEqual(None,get_location_field_code(form_model))

    def _get_form_model(self, is_registration_form=False):
        self.dbm=Mock(spec=DatabaseManager)
        self.form_code="form_code"
        return FormModel(dbm=self.dbm, form_code=self.form_code, name="abc", fields=[],
            is_registration_model=is_registration_form, entity_type=["entity_type"])

    def _get_location_field(self):
        location_field = HierarchyField(name=LOCATION_TYPE_FIELD_NAME, code=LOCATION_TYPE_FIELD_CODE,
            label="anything",
            language="en", ddtype=Mock(spec=DataDictType))

        return location_field

    def _get_text_field(self):
        anything = "anything"
        text_field = TextField(name=anything, code=anything, label=anything,
            ddtype=Mock(spec=DataDictType),
            instruction=anything)
        return text_field

