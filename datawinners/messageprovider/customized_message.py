from datawinners.common.lang.utils import questionnaire_customized_message_details, account_wide_customized_message_details
from mangrove.form_model.form_model import get_form_model_by_code, EntityFormModel
from mangrove.form_model.project import Project


def _replace_placeholders_in_message(message, placeholder_dict):
    for key, value in placeholder_dict.iteritems():
        message = message.replace('{<{%s}>}' % key, value)
    return message


def get_customized_message_for_questionnaire(dbm, request, message_code, form_code, placeholder_dict=None, form_model=None):
    if form_model is None:
        try:
            form_model = get_form_model_by_code(dbm, form_code)
        except:
            pass

    if form_model is None or isinstance(form_model, EntityFormModel): #For UniqueId registration
        message = _get_customized_message_for_language(dbm, request.get('organization').language, message_code)
    else: # For questionnaire submission
        project = Project.from_form_model(form_model)
        message = _get_customized_message_for_language(dbm, project.language, message_code)
        request['is_outgoing_reply_sms_enabled'] = project.is_outgoing_sms_replies_enabled

    if placeholder_dict:
        message = _replace_placeholders_in_message(message, placeholder_dict)
    return message


def _get_customized_message_for_language(dbm, language, message_code):
    reply_message_list = questionnaire_customized_message_details(dbm, language)
    return len(reply_message_list)
    return [reply_message['message'] for reply_message in reply_message_list if
                   reply_message['code'] == message_code][0]

def get_account_wide_sms_reply(dbm, message_code, placeholder_dict=None):
    reply_message_list = account_wide_customized_message_details(dbm)
    message = [reply_message['message'] for reply_message in reply_message_list if
                   reply_message['code'] == message_code][0]
    if placeholder_dict:
        message = _replace_placeholders_in_message(message,placeholder_dict)
    return message
