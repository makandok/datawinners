import json

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.utils.translation import ugettext

from datawinners.accountmanagement.decorators import session_not_expired, is_datasender, is_not_expired
from datawinners.entity.group_helper import get_group_details
from datawinners.main.database import get_database_manager
from datawinners.search.all_datasender_search import get_all_datasenders_short_codes
from mangrove.datastore.entity import contact_by_short_code


@login_required
@session_not_expired
@is_datasender
@is_not_expired
def get_group_names(request):
    dbm = get_database_manager(request.user)
    group_names = get_group_details(dbm)
    return HttpResponse(json.dumps({'group_names': group_names}), content_type="application/json")


def _update_group_for_contacts(contact_ids, dbm, group_names):
    for contact_id in contact_ids:
        contact = contact_by_short_code(dbm, contact_id)
        for group_name in group_names:
            contact.add_custom_group(group_name)
        contact.save()


@login_required
@session_not_expired
@is_datasender
@is_not_expired
def assign_contact_to_groups(request):
    dbm = get_database_manager(request.user)
    group_names = json.loads(request.POST['group-names'])
    current_group_name = request.POST['current_group_name']
    contact_ids = json.loads(request.POST['contact_ids'])
    all_selected = json.loads(request.POST['all_selected'])
    success = True
    try:
        if not all_selected:
            _update_group_for_contacts(contact_ids, dbm, group_names)
        else:
            search_query= request.POST['search_query']
            contact_ids = _get_reporter_ids_for_group_name(dbm, current_group_name, search_query)
            _update_group_for_contacts(contact_ids, dbm, group_names)
        message = ugettext('The Contact(s) are added to Group(s) successfully.')
    except Exception:
        # log exception
        message = ugettext('Failed to add in to group.')
        success = False
    return HttpResponse(content=json.dumps({'success': success, 'message':message}), content_type='application/json')


def _get_reporter_ids_for_group_name(dbm, group_name, search_query):
        search_parameters = {'search_filter': {'group_name': group_name, 'search_text': search_query}}
        return get_all_datasenders_short_codes(dbm, search_parameters)