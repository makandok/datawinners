from django.utils import translation

from datawinners.messageprovider.handlers import data_sender_not_linked_handler, data_sender_not_registered_handler
from mangrove.contrib.registration import GLOBAL_REGISTRATION_FORM_CODE
from mangrove.datastore.documents import ProjectDocument
from mangrove.errors.MangroveException import SMSParserWrongNumberOfAnswersException, NumberNotRegisteredException, \
    FormModelDoesNotExistsException, ProjectPollCodeDoesNotExistsException
from mangrove.errors.MangroveException import ExceedSMSLimitException, ExceedSubmissionLimitException
from mangrove.errors.MangroveException import DatasenderIsNotLinkedException
from mangrove.form_model.form_model import get_form_model_by_code, FORM_CODE
from mangrove.form_model.project import Project, get_active_form_model, get_project_by_code, check_if_form_model_is_poll
from mangrove.transport.contract.response import Response
from mangrove.form_model.form_model import EntityFormModel
from datawinners.messageprovider.messages import get_wrong_number_of_answer_error_message


class PostSMSProcessorLanguageActivator(object):
    def __init__(self, dbm, request):
        self.dbm = dbm
        self.request = request

    def process(self, form_code, submission_values):
        self.request[FORM_CODE] = form_code
        try:
            form_model = get_form_model_by_code(self.dbm, form_code)
        except FormModelDoesNotExistsException:
            form_model = get_active_form_model(self.dbm, form_code)
        if not isinstance(form_model, EntityFormModel):
            translation.activate(form_model.activeLanguages[0])
        else:
            self.request['is_registration'] = True

class PostSMSProcessorCheckDSIsRegistered(object):
    def __init__(self, dbm, request):
        self.dbm = dbm
        self.request = request

    def _get_response(self):
        response = Response(reporters=[], survey_response_id=None)
        response.errors = data_sender_not_registered_handler(self.dbm, self.request)
        return response

    def process(self, form_code, submission_values):
        try:
            form_model = get_form_model_by_code(self.dbm, form_code)
        except FormModelDoesNotExistsException:
            form_model = get_active_form_model(self.dbm, form_code)
        exception = self.request.get('exception')
        if exception and isinstance(exception, NumberNotRegisteredException) and not form_model.is_open_survey:
           return self._get_response()


class PostSMSProcessorNumberOfAnswersValidators(object):
    def __init__(self, dbm, request):
        self.dbm = dbm
        self.request = request

    def process(self, form_code, submission_values, extra_data=[]):
        try:
            form_model = get_form_model_by_code(self.dbm, form_code)
            check_if_form_model_is_poll(self, form_model)
        except FormModelDoesNotExistsException:
            form_model = get_active_form_model(self.dbm, form_code)

        processor_func = self._get_handlers(form_model)
        response = processor_func(form_model, submission_values)
        if len(extra_data) or (response and not response.success):
            self.request['exception'] = SMSParserWrongNumberOfAnswersException(form_code)


    def _get_handlers(self, form_model):
        if form_model.is_entity_registration_form():
            return self._process_registration_request
        else:
            return self._process_data_submission_request

    def _get_wrong_number_of_question_response(self):
        response = Response(reporters=[], survey_response_id=None)
        response.success = False
        response.errors = get_wrong_number_of_answer_error_message()
        return response

    def _process_registration_when_entity_question_is_present(self, form_model, submission_values):
        # the answer to short code question may or may not present
        if (self._correct_number_of_questions_with_short_code_present(form_model, submission_values)) or (
            self._correct_number_of_questions_with_short_code_absent(form_model, submission_values)):
            return None
        return self._get_wrong_number_of_question_response()

    def _correct_number_of_questions_with_short_code_present(self, form_model, submission_values):
        return len(form_model.fields) == len(submission_values.keys())

    def _correct_number_of_questions_with_short_code_absent(self, form_model, submission_values):
        if form_model.is_entity_registration_form():
            return len(form_model.fields) == len(submission_values.keys()) + 1
        return False

    def _process_registration_when_entity_question_is_absent(self, form_model, submission_values):
        if len(form_model.fields) != len(submission_values.keys()):
            return self._get_wrong_number_of_question_response()

    def _process_registration_request(self, form_model, submission_values):
        if form_model.form_code == GLOBAL_REGISTRATION_FORM_CODE:
            return None

        if form_model.entity_questions:
            return self._process_registration_when_entity_question_is_present(form_model, submission_values)
        else:
            return self._process_registration_when_entity_question_is_absent(form_model, submission_values)

    def _process_data_submission_request(self, form_model, submission_values):
        return self._process_registration_when_entity_question_is_present(form_model, submission_values)

class PostSMSProcessorCheckDSIsLinkedToProject(object):
    def __init__(self, dbm, request):
        self.dbm = dbm
        self.request = request

    def _get_response(self, form_code):
        response = Response(reporters=[], survey_response_id=None, exception=self._get_exception())
        response.success = True
        response.errors = data_sender_not_linked_handler(self.dbm, self.request, form_code=form_code)
        return response


    def process(self, form_code, submission_values):
        try:
            form_model = get_form_model_by_code(self.dbm, form_code)
        except FormModelDoesNotExistsException:
            form_model = get_active_form_model(self.dbm, form_code)
        project = Project.from_form_model(form_model=form_model)
        reporter_entity = self.request.get('reporter_entity')

        if project.is_open_survey or (reporter_entity.short_code == "test" or \
                isinstance(form_model, EntityFormModel) or \
                        reporter_entity.short_code in Project.from_form_model(form_model).data_senders):
            self.check_answers_numbers(is_poll=project.is_poll, submission_values=submission_values)
            return None

        self.check_answers_numbers(is_poll=project.is_poll, submission_values=submission_values, linked_datasender=False)
        return self._get_response(form_code)

    def check_answers_numbers(self, is_poll, submission_values, linked_datasender=True):
        exception = self.request.get('exception', False)
        if exception and isinstance(exception, SMSParserWrongNumberOfAnswersException):
            if linked_datasender:
                raise exception
            raise self._get_exception()
        elif not linked_datasender and is_poll:
            raise FormModelDoesNotExistsException(submission_values['q1'])

    def _get_exception(self):
        datasender = self.request.get('reporter_entity')
        return DatasenderIsNotLinkedException(datasender.value('name'), datasender.short_code)



class PostSMSProcessorCheckLimits(object):
    def __init__(self, dbm, request):
        self.dbm = dbm
        self.request = request

    def process(self, form_code, submission_values):
        exception = self.request.get('exception')
        form_model = get_form_model_by_code(self.dbm, form_code)
        if exception and (
                isinstance(exception, ExceedSubmissionLimitException) or isinstance(exception, ExceedSMSLimitException)):
            if not self.request.get('organization').has_exceeded_message_limit() and isinstance(form_model, EntityFormModel):
                return
            raise exception
