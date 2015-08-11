import json
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.utils.translation import ugettext as _, ugettext
from django.views.decorators.csrf import csrf_exempt
from datawinners.accountmanagement.decorators import session_not_expired, is_not_expired
from datawinners.accountmanagement.models import NGOUserProfile,\
    get_ngo_admin_user_profiles_for
from datawinners.activitylog.models import UserActivityLog
from datawinners.common.constant import CREATED_QUESTIONNAIRE
from datawinners.main.database import get_database_manager
from datawinners.project import helper
from datawinners.project.helper import associate_account_users_to_project
from datawinners.project.wizard_view import get_preview_and_instruction_links, create_questionnaire
from datawinners.utils import get_organization
from mangrove.datastore.entity_type import get_unique_id_types
from mangrove.errors.MangroveException import QuestionCodeAlreadyExistsException, QuestionAlreadyExistsException, EntityQuestionAlreadyExistsException
from mangrove.form_model.project import get_active_form_model_name_and_id
from mangrove.datastore.user_permission import grant_user_permission_for,\
    get_user_permission


@login_required
@session_not_expired
@csrf_exempt
@is_not_expired
def create_project(request):
    manager = get_database_manager(request.user)
    org = get_organization(request)
    is_active, project_active_id, project_active_name = get_active_form_model_name_and_id(manager)
    has_permission_on_active_project = True
    ngo_admin_email = get_ngo_admin_user_profiles_for(org)[0].user.email
    if is_active:
        user_permission = get_user_permission(user_id=request.user.id, dbm=manager)
        if not project_active_id in user_permission.project_ids:
            has_permission_on_active_project = False
    
    if request.method == 'GET':
        cancel_link = reverse('dashboard') if request.GET.get('prev', None) == 'dash' else reverse('alldata_index')
        return render_to_response('project/create_project.html',
                                  {'preview_links': get_preview_and_instruction_links(),
                                   'questionnaire_code': helper.generate_questionnaire_code(manager),
                                   'is_edit': 'false',
                                   'is_pro_sms': org.is_pro_sms,
                                   'active_language': request.LANGUAGE_CODE,
                                   'post_url': reverse(create_project),
                                   'unique_id_types': json.dumps([unique_id_type.capitalize() for unique_id_type in
                                                                  get_unique_id_types(manager)]),
                                   'has_permission_on_active_project':has_permission_on_active_project,
                                   'ngo_admin_email':ngo_admin_email,
                                   'cancel_link': cancel_link, 'is_active': is_active, 'project_active_id': project_active_id, 'project_active_name': project_active_name}, context_instance=RequestContext(request))

    if request.method == 'POST':
        response_dict = _create_project_post_response(request, manager)
        return HttpResponse(json.dumps(response_dict))


def validate_questionnaire_name_and_code(questionnaire, org):
    code_has_errors, name_has_errors = False, False
    error_message = {}
    if not questionnaire.is_form_code_unique():
        code_has_errors = True
        error_message["code"] = _("Questionnaire with same code already exists.")
    if not questionnaire.is_project_name_unique():
        name_has_errors = True
        if org.is_pro_sms:
            error_message["name"] = _("Questionnaire or Poll with same name already exists.")
        else:
            error_message["name"] = _("Questionnaire with same name already exists.")
    return code_has_errors, error_message, name_has_errors


def _is_open_survey_allowed(request, is_open_survey):
    return get_organization(request).is_pro_sms and is_open_survey


def _create_project_post_response(request, manager):
    project_info = json.loads(request.POST['profile_form'])
    try:
        ngo_admin = NGOUserProfile.objects.get(user=request.user)
        is_open_survey_allowed = _is_open_survey_allowed(request, request.POST.get('is_open_survey'))
        questionnaire = create_questionnaire(post=request.POST, manager=manager, name=project_info.get('name'),
                                             language=project_info.get('language', request.LANGUAGE_CODE),
                                             reporter_id=ngo_admin.reporter_id,
                                             is_open_survey=is_open_survey_allowed)
    except (QuestionCodeAlreadyExistsException, QuestionAlreadyExistsException,
            EntityQuestionAlreadyExistsException) as ex:
        return {'success': False, 'error_message': _(ex.message), 'error_in_project_section': False}

    org = get_organization(request)

    code_has_errors, error_message, name_has_errors = validate_questionnaire_name_and_code(questionnaire, org)

    if not code_has_errors and not name_has_errors:
        associate_account_users_to_project(manager, questionnaire)
        questionnaire.update_doc_and_save()
        grant_user_permission_for(user_id=request.user.id, questionnaire_id=questionnaire.id, manager=manager)
        UserActivityLog().log(request, action=CREATED_QUESTIONNAIRE, project=questionnaire.name,
                              detail=questionnaire.name)
        return {'success': True, 'project_id': questionnaire.id}

    return {'success': False,
            'error_message': error_message,
            'error_in_project_section': False,
            'code_has_errors': code_has_errors,
            'name_has_errors': name_has_errors}
    
