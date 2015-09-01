from datetime import datetime
import logging
import urllib2

from django.conf import settings
from django.http import HttpResponse
import jsonpickle
from mangrove.datastore.user_permission import has_permission
from datawinners.common.authorization import httpbasic, is_not_datasender

from datawinners.main.database import get_database_manager
from datawinners.dataextraction.helper import convert_to_json_response
from datawinners.feeds.database import get_feeds_database
from mangrove.errors.MangroveException import FormModelDoesNotExistsException
from mangrove.form_model.form_model import get_form_model_by_code

DATE_FORMAT = '%d-%m-%Y %H:%M:%S'


def stream_feeds(feed_dbm, startkey, endkey):
    rows = feed_dbm.database.iterview("questionnaire_feed/questionnaire_feed", 1000, startkey=startkey, endkey=endkey)
    first = True
    yield "["
    for row in rows:
        yield '' if first else ","
        yield jsonpickle.encode(row['value'], unpicklable=False)
        first = False
    yield "]"


@httpbasic
@is_not_datasender
def feed_entries(request, form_code):
    user = request.user
    try:
        if not settings.FEEDS_ENABLED:
            return HttpResponse(404)
        if invalid_date(request.GET.get('start_date')):
            return convert_to_json_response(
                {"ERROR_CODE": 102, "ERROR_MESSAGE": 'Invalid Start Date provided'}, 400)
        if invalid_date(request.GET.get('end_date')):
            return convert_to_json_response(
                {"ERROR_CODE": 102, "ERROR_MESSAGE": 'Invalid End Date provided'}, 400)
        if lesser_end_date(request.GET.get('end_date'), request.GET.get('start_date')):
            return convert_to_json_response(
                {"ERROR_CODE": 103, "ERROR_MESSAGE": 'End Date provided is less than Start Date'}, 400)
        if _invalid_form_code(request, form_code):
            return convert_to_json_response({"ERROR_CODE": 101, "ERROR_MESSAGE": 'Invalid form code provided'}, 400)

        dbm = get_database_manager(user)
        form_model = get_form_model_by_code(dbm, form_code)
        questionnaire_id = form_model.id
        if user.can_manage_questionnaire(questionnaire_id):
            feed_dbm = get_feeds_database(request.user)
            start_date = _parse_date(request.GET['start_date'])
            end_date = _parse_date(request.GET['end_date'])
            return HttpResponse(stream_feeds(feed_dbm, startkey=[form_code, start_date], endkey=[form_code, end_date]),
                                content_type='application/json; charset=utf-8')

        return convert_to_json_response({"ERROR_CODE": 104, "ERROR_MESSAGE": "You don't have access to this feed"}, 403)
    except Exception as e:
        logger = logging.getLogger('datawinners')
        logger.exception(e)
        return HttpResponse(content='Internal Server Error', status=500)


def _is_empty_string(value):
    return value is None or value.strip() == ''


def _invalid_form_code(request, form_code):
    try:
        dbm = get_database_manager(request.user)
        get_form_model_by_code(dbm, form_code)
        return False
    except FormModelDoesNotExistsException as e:
        return True


def _parse_date(date):
    date_string = urllib2.unquote(date.strip())
    return datetime.strptime(date_string, DATE_FORMAT)


def invalid_date(date_string):
    if _is_empty_string(date_string):
        return True
    try:
        _parse_date(date_string)
    except ValueError:
        return True
    return False


def lesser_end_date(end_date, start_date):
    end_date = _parse_date(end_date)
    start_date = _parse_date(start_date)
    return end_date < start_date
