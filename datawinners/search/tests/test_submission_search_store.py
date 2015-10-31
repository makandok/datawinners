import unittest

from mock import Mock, MagicMock, patch

from mangrove.datastore.database import DatabaseManager
from datawinners.search.submission_index import SubmissionSearchStore, FieldTypeChangeException
from mangrove.form_model.field import DateField, UniqueIdField
from mangrove.form_model.form_model import FormModel, EntityFormModel


class TestSubmissionSearchStore(unittest.TestCase):
    def setUp(self):
        self.dbm = Mock(spec=DatabaseManager)
        fields = [DateField(name='q3', code='q3', label='Reporting date', date_format='dd.mm.yyyy'),
             UniqueIdField(unique_id_type='clinic',name="Q1", code="EID", label="What is the clinic id?")]
        self.form_model = FormModel(self.dbm, "abc", "abc", form_code="cli001", fields=fields)
        self.dbm = MagicMock(spec=DatabaseManager)
        dbm_view = MagicMock()
        self.dbm.database_name = 'somedb'
        self.dbm.view = dbm_view
        self.es = Mock()

    def test_should_add_es_mapping_when_no_existing_questions_mapping(self):
        no_old_mapping = []
        es_mock = MagicMock()
        form_model_mock = MagicMock()

        with patch("datawinners.search.submission_index.get_elasticsearch_handle") as get_elasticsearch_handle_mock:
            get_elasticsearch_handle_mock.return_value = es_mock
            es_mock.get_mapping.return_value = no_old_mapping
            self.dbm.view.registration_form_model_by_entity_type.return_value = []
            # form_model_mock.return_value = EntityFormModel(self.dbm, name='clinic',
            #                                                form_code='cli', fields=[])

            SubmissionSearchStore(self.dbm, self.form_model, self.form_model).update_store()

        self.assertTrue(es_mock.put_mapping.called)

    def test_should_throw_exception_when_unique_id_type_field_changes(self):
        new_fields = [DateField(name='q3', code='q3', label='Reporting date', date_format='dd.mm.yyyy'),
                      UniqueIdField(unique_id_type='student', name="Q1", code="EID", label="What is the student id?")]
        latest_form_model = FormModel(self.dbm, "abc", "abc", form_code="cli001", fields=new_fields)
        es_mock = MagicMock()

        with patch("datawinners.search.submission_index.get_elasticsearch_handle") as get_elasticsearch_handle_mock:
            with self.assertRaises(FieldTypeChangeException) as e:
                get_elasticsearch_handle_mock.return_value = es_mock

                SubmissionSearchStore(self.dbm, latest_form_model, self.form_model)._verify_unique_id_change()

    def test_should_throw_exception_when_unique_id_type_field_code_changes(self):
        new_fields = [DateField(name='q3', code='q3', label='Reporting date', date_format='dd.mm.yyyy'),
                      UniqueIdField(unique_id_type='clinic', name="Q1", code="EID new", label="What is the clinic id?")]
        latest_form_model = FormModel(self.dbm, "abc", "abc", form_code="cli001", fields=new_fields)
        es_mock = MagicMock()

        with patch("datawinners.search.submission_index.get_elasticsearch_handle") as get_elasticsearch_handle_mock:
            with self.assertRaises(FieldTypeChangeException) as e:
                get_elasticsearch_handle_mock.return_value = es_mock

                SubmissionSearchStore(self.dbm, latest_form_model, self.form_model)._verify_unique_id_change()

    def test_should_throw_exception_when_unique_id_field_removed(self):
        new_fields = [DateField(name='q3', code='q3', label='Reporting date', date_format='dd.mm.yyyy')]
        latest_form_model = FormModel(self.dbm, "abc", "abc", form_code="cli001", fields=new_fields)
        es_mock = MagicMock()

        with patch("datawinners.search.submission_index.get_elasticsearch_handle") as get_elasticsearch_handle_mock:
            with self.assertRaises(FieldTypeChangeException) as e:
                get_elasticsearch_handle_mock.return_value = es_mock

                SubmissionSearchStore(self.dbm, latest_form_model, self.form_model)._verify_unique_id_change()

    def test_should_not_throw_exception_when_unique_id_field_reordered(self):
        new_fields = [UniqueIdField(unique_id_type='clinic', name="Q1", code="EID", label="What is the clinic id?"),
                      DateField(name='q3', code='q3', label='Reporting date', date_format='dd.mm.yyyy')]
        es_mock = MagicMock()
        latest_form_model = FormModel(self.dbm, "abc", "abc", form_code="cli001", fields=new_fields)

        with patch("datawinners.search.submission_index.get_elasticsearch_handle") as get_elasticsearch_handle_mock:
            get_elasticsearch_handle_mock.return_value = es_mock

            SubmissionSearchStore(self.dbm, latest_form_model, self.form_model)._verify_unique_id_change()

            self.assertFalse(self.es.put_mapping.called)
