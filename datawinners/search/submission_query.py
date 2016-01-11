import json
import datetime

from django.utils.translation import ugettext, get_language

from datawinners.accountmanagement.localized_time import convert_utc_to_localized
from datawinners.search.index_utils import es_unique_id_code_field_name, es_questionnaire_field_name, safe_getattr
from datawinners.search.submission_index_constants import SubmissionIndexConstants
from mangrove.form_model.field import FieldSet, SelectField, MediaField, PhotoField, UniqueIdField


class SubmissionQueryResponseCreator(object):
    def __init__(self, form_model, localized_time_delta):
        self.form_model = form_model
        self.localized_time_delta = localized_time_delta

    def combine_name_and_id(self, short_code, entity_name, submission):
        return submission.append(
            ["%s<span class='small_grey'>  %s</span>" % (
                entity_name, short_code)]) if entity_name else submission.append(entity_name)

    def get_field_set_fields(self, fields, parent_field_code=None):
        field_set_field_dict = {}
        for field in fields:
            if isinstance(field, FieldSet):
                field_set_field_dict.update(
                    {es_questionnaire_field_name(field.code, self.form_model.id, parent_field_code): field})
                group_field_code = field.code if field.is_group() else None
                field_set_field_dict.update(self.get_field_set_fields(field.fields, group_field_code))
        return field_set_field_dict

    def _populate_datasender(self, res, submission):
        if safe_getattr(res, SubmissionIndexConstants.DATASENDER_ID_KEY) == u'N/A':
            submission.append(safe_getattr(res, SubmissionIndexConstants.DATASENDER_NAME_KEY))
        else:
            self.combine_name_and_id(safe_getattr(res, SubmissionIndexConstants.DATASENDER_ID_KEY),
                                     safe_getattr(res, SubmissionIndexConstants.DATASENDER_NAME_KEY), submission)

    def _populate_error_message(self, key, language, res, submission):
        error_msg = safe_getattr(res, key)
        if error_msg.find('| |') != -1:
            error_msg = error_msg.split('| |,')[['en', 'fr'].index(language)]
        submission.append(error_msg)

    def _convert_to_localized_date_time(self, key, res, submission):
        submission_date_time = datetime.datetime.strptime(safe_getattr(res, key), "%b. %d, %Y, %I:%M %p")
        datetime_local = convert_utc_to_localized(self.localized_time_delta, submission_date_time)
        submission.append(datetime_local.strftime("%b. %d, %Y, %H:%M"))

    def _get_media_field_codes(self):
        return [es_questionnaire_field_name(field.code, self.form_model.id, field.parent_field_code) for
                field in
                self.form_model.media_fields] if self.form_model.is_media_type_fields_present else []

    def _get_image_field_codes(self):
        media_field_code = []
        for media_field in self.form_model.media_fields:
            if isinstance(media_field, PhotoField):
                media_field_code.append(
                    es_questionnaire_field_name(media_field.code, self.form_model.id, media_field.parent_field_code))
        return media_field_code

    def _traverse_aggregation_buckets(self, search_results, aggr_result):
        if not hasattr(search_results['tag'], 'buckets'):
            aggr_result.extend(search_results['tag']['hits']['hits'])
        else:
            for bucket in search_results['tag'].buckets:
                self._traverse_aggregation_buckets(bucket, aggr_result)

    def create_response(self, required_field_names, search_results):
        entity_question_codes = [es_questionnaire_field_name(field.code, self.form_model.id, field.parent_field_code)
                                 for field in
                                 self.form_model.entity_questions]
        fieldset_fields = self.get_field_set_fields(self.form_model.fields)
        meta_fields = [SubmissionIndexConstants.DATASENDER_ID_KEY]
        meta_fields.extend([es_unique_id_code_field_name(code) for code in entity_question_codes])
        media_field_codes = self._get_media_field_codes()
        image_fields = self._get_image_field_codes()
        submissions = []
        language = get_language()

        if hasattr(search_results, 'aggregations'):
            aggr_result = []
            self._traverse_aggregation_buckets(search_results.aggregations, aggr_result)
            for res in aggr_result:
                submission = [res._id]
                res = res._source
                self._append_to_submission(entity_question_codes, fieldset_fields, image_fields, language,
                                           media_field_codes, meta_fields, required_field_names, res, submission)
                submissions.append(submission)
            return submissions, len(aggr_result)
        else:
            for res in search_results.hits:
                submission = [res.meta.id]
                self._append_to_submission(entity_question_codes, fieldset_fields, image_fields, language,
                                           media_field_codes, meta_fields, required_field_names, res, submission)
                submissions.append(submission)
            return submissions, search_results.hits.total

    def _append_to_submission(self, entity_question_codes, fieldset_fields, image_fields, language, media_field_codes,
                              meta_fields, required_field_names, res, submission):
        for key in required_field_names:
            if key not in meta_fields:
                if key in entity_question_codes:
                    self.combine_name_and_id(
                        short_code=safe_getattr(res, es_unique_id_code_field_name(key)),
                        entity_name=safe_getattr(res, key), submission=submission)
                elif key == SubmissionIndexConstants.DATASENDER_NAME_KEY:
                    self._populate_datasender(res, submission)
                elif key == 'status':
                    submission.append(ugettext(safe_getattr(res, key)))
                elif key == SubmissionIndexConstants.SUBMISSION_DATE_KEY:
                    self._convert_to_localized_date_time(key, res, submission)
                elif key == 'error_msg':
                    self._populate_error_message(key, language, res, submission)
                elif key in fieldset_fields.keys():
                    submission.append(
                        _format_fieldset_values_for_representation(safe_getattr(res, key),
                                                                   fieldset_fields.get(key),
                                                                   res.meta.id))
                else:
                    submission.append(
                        self._append_if_attachments_are_present(res, key, media_field_codes, image_fields))

    def _append_if_attachments_are_present(self, res, key, media_field_codes, image_fields):
        if self.form_model.is_media_type_fields_present and key in media_field_codes:
            if key in image_fields:
                return _format_media_value(res.meta.id, safe_getattr(res, key), thumbnail_flag=True)
            else:
                return _format_media_value(res.meta.id, safe_getattr(res, key))

        else:
            return safe_getattr(res, ugettext(key))


def _format_media_value(submission_id, value, thumbnail_flag=False):
    formatted_value = ""
    if thumbnail_flag:
        formatted_value = "<img src='/download/attachment/%s/preview_%s' alt=''/>" % (submission_id, value)
    if value:
        return formatted_value + "  <a href='/download/attachment/%s/%s'>%s</a>" % (submission_id, value, value)


def _format_values(field_set, formatted_value, value_list, submission_id):
    if not value_list:
        return ''
    value_dict = value_list[0]
    for i, field in enumerate(field_set.fields):
        if isinstance(field, SelectField):
            choices = value_dict.get(field.code)
            if choices:
                if field.is_single_select:
                    value = choices
                else:
                    value = '(' + ', '.join(choices) + ')' if len(choices) > 1 else ', '.join(choices)
            else:
                value = ''
        elif isinstance(field, FieldSet):
            value = ''
            value = _format_values(field, value, value_dict.get(field.code), submission_id)
        elif isinstance(field, MediaField):
            show_thumbnail = isinstance(field, PhotoField)
            value = _format_media_value(submission_id, value_dict.get(field.code), show_thumbnail)
            value = '' if not value else value
        elif isinstance(field, UniqueIdField):
            value = value_dict.get(field.code) + ' (' + value_dict.get(field.code + '_unique_code') + ')'

        else:
            value = value_dict.get(field.code) or ''
        formatted_value += '"' + '<span class="repeat_qtn_label">' + field.label + '</span>' + ': ' + value + '"'
        formatted_value += ';' if i == len(field_set.fields) - 1 else ', '
    return formatted_value


def _format_fieldset_values_for_representation(entry, field_set, submission_id):
    formatted_value = ''
    if entry:
        for value_dict in json.loads(entry):
            formatted_value = _format_values(field_set, formatted_value, [value_dict], submission_id)
            formatted_value += '<br><br>'
        return '<span class="repeat_ans">' + formatted_value + '</span>'
