from elasticsearch import Elasticsearch, helpers
from elasticsearch_dsl import Search, Q, F
import elasticutils
from datawinners.search.filters import SubmissionDateRangeFilter, DateQuestionRangeFilter
from datawinners.search.index_utils import es_unique_id_code_field_name, es_questionnaire_field_name
from datawinners.search.query import ElasticUtilsHelper
from datawinners.search.submission_headers import HeaderFactory
from datawinners.settings import ELASTIC_SEARCH_URL, ELASTIC_SEARCH_TIMEOUT, ELASTIC_SEARCH_HOST, ELASTIC_SEARCH_PORT
import logging

logger = logging.getLogger("datawinners")

def _add_sort_criteria(search_parameters, search):
    if 'sort_field' not in search_parameters:
        return search

    order_by_field = "%s_value" % search_parameters["sort_field"]
    order = search_parameters.get("order")
    order_by_criteria = "-" + order_by_field if order == '-' else order_by_field
    return search.sort(order_by_criteria)


def _add_pagination_criteria(search_parameters, search):
    start_result_number = search_parameters.get("start_result_number")
    number_of_results = search_parameters.get("number_of_results")
    return search.extra(from_=start_result_number, size=number_of_results)


def _query_by_submission_type(submission_type_filter, search):
    if submission_type_filter == 'deleted':
        return search.query('term', void=True)
    elif submission_type_filter == 'all':
        return search.query('term', void=False)

    if submission_type_filter == 'analysis':
        search = search.query('term', status='success')
    else:
        search = search.query('term', status=submission_type_filter)
    return search.query('term', void=False)


def _get_query_fields(form_model, submission_type):
    header = HeaderFactory(form_model).create_header(submission_type)
    return header.get_header_field_names()


def _add_date_range_filters(date_filters, form_model, search):
    if date_filters:
        for question_code, date_range in date_filters.items():
            if date_range:
                date_query = DateQuestionRangeFilter(date_range, form_model, question_code).build_filter_query()
                if date_query:
                    search = search.query(date_query)
    return search


def _add_unique_id_filters(form_model, unique_id_filters, search):
    if unique_id_filters:
        for uniqueIdType, uniqueIdFilter in unique_id_filters.iteritems():
            if uniqueIdFilter:
                unique_id_filters = []

                for question in [question for question in form_model.entity_questions if
                                 question.unique_id_type == uniqueIdType]:
                    es_field_code = es_unique_id_code_field_name(
                        es_questionnaire_field_name(question.code, form_model.id, parent_field_code=question.parent_field_code)) + "_exact"
                    unique_id_filters.append(F("term", **{es_field_code: uniqueIdFilter}))
                search = search.filter(F('or', unique_id_filters))
    return search


def _add_search_filters(search_filter_param, form_model, local_time_delta, query_fields, search):
    if not search_filter_param:
        return

    query_text = search_filter_param.get("search_text")
    query_text_escaped = ElasticUtilsHelper().replace_special_chars(query_text)
    if query_text:
        search = search.query("query_string", query=query_text_escaped, fields=query_fields)
    submission_date_range = search_filter_param.get("submissionDatePicker")
    submission_date_query = SubmissionDateRangeFilter(submission_date_range, local_time_delta).build_filter_query()
    if submission_date_query:
        search = search.query(submission_date_query)
    search = _add_date_range_filters(search_filter_param.get("dateQuestionFilters"), form_model, search)
    datasender_filter = search_filter_param.get("datasenderFilter")
    if datasender_filter:
        search = search.query("term", ds_id_exact=datasender_filter)
    search = _add_unique_id_filters(form_model, search_filter_param.get("uniqueIdFilters"), search)
    return search


def _add_filters(form_model, search_parameters, local_time_delta, search):
    search = _query_by_submission_type(search_parameters.get('filter'), search)
    query_fields = _get_query_fields(form_model, search_parameters.get('filter'))
    search = _add_search_filters(search_parameters.get('search_filters'), form_model, local_time_delta, query_fields,
                                 search)
    return query_fields, search


def _query_for_questionnaire(dbm, form_model):
    return elasticutils.S().es(urls=ELASTIC_SEARCH_URL, timeout=ELASTIC_SEARCH_TIMEOUT).indexes(
        dbm.database_name).doctypes(form_model.id)


def _add_response_fields(search_parameters, search):
    if 'response_fields' in search_parameters:
        search = search.fields(search_parameters['response_fields'])
    return search


def _create_query(dbm, form_model, local_time_delta, search_parameters):
    es = Elasticsearch(hosts=[{"host": ELASTIC_SEARCH_HOST, "port": ELASTIC_SEARCH_PORT}])
    search = Search(using=es, index=dbm.database_name, doc_type=form_model.id)
    search = _add_pagination_criteria(search_parameters, search)
    search = _add_sort_criteria(search_parameters, search)
    search = _add_response_fields(search_parameters, search)
    query_fields, search = _add_filters(form_model, search_parameters, local_time_delta, search)
    return query_fields, search


def get_submissions_paginated(dbm, form_model, search_parameters, local_time_delta):
    query_fields, search = _create_query(dbm, form_model, local_time_delta, search_parameters)
    search_results = search.execute()
    return search_results, query_fields

def get_submissions_paginated_simple(dbm, form_model, pagination_params, sort_params=None):
    pagination_params = _transform_params_based_on_type(pagination_params)
    es = Elasticsearch(hosts=[{"host": ELASTIC_SEARCH_HOST, "port": ELASTIC_SEARCH_PORT}])
    search = Search(using=es, index=dbm.database_name, doc_type=form_model.id)
    search = search.sort(sort_params)
    search = search.extra(**pagination_params)
    search_results = None
    try:
        search_results = search.execute()
    except:
        logger.exception('Exception happened while fetching analysis data')
    return search_results

def _transform_params_based_on_type(params):
    transformed_params = {}
    for key in params:
        if isinstance( params[key], basestring ) and params[key].isdigit():
            transformed_params[key] = int(params[key])
        else:
            transformed_params[key] = params[key]
    return transformed_params

def get_scrolling_submissions_query(dbm, form_model, search_parameters, local_time_delta):
    """
    Efficient way to fetch large number of submissions from ElasticSearch
    """
    query_fields, search = _create_query(dbm, form_model, local_time_delta, search_parameters)
    query_dict = search.to_dict()
    # if search_parameters.get('get_only_id', False):
    #     query_dict["fields"] = []
    scan_response = helpers.scan(client=Elasticsearch(hosts=[{"host": ELASTIC_SEARCH_HOST, "port": ELASTIC_SEARCH_PORT}]), index=dbm.database_name, doc_type=form_model.id,
                                 query=query_dict, timeout="3m", size=4000)
    return scan_response, query_fields


def get_submissions_without_user_filters_count(dbm, form_model, search_parameters):
    es = Elasticsearch(hosts=[{"host": ELASTIC_SEARCH_HOST, "port": ELASTIC_SEARCH_PORT}])
    search = Search(using=es, index=dbm.database_name, doc_type=form_model.id)
    search = _query_by_submission_type(search_parameters.get('filter'), search)
    body = search.to_dict()
    return es.search(index=dbm.database_name, doc_type=form_model.id, body=body, search_type='count')['hits']['total']


def get_submission_count(dbm, form_model, search_parameters, local_time_delta):
    es = Elasticsearch(hosts=[{"host": ELASTIC_SEARCH_HOST, "port": ELASTIC_SEARCH_PORT}])
    search = Search(using=es, index=dbm.database_name, doc_type=form_model.id)
    query_fields, search = _add_filters(form_model, search_parameters, local_time_delta, search)
    body = search.to_dict()
    return es.search(index=dbm.database_name, doc_type=form_model.id, body=body, search_type='count')['hits']['total']


def _get_facet_result(facet_response, field_name):
    facet_result_options = []
    facet_result = {
        "es_field_name": field_name,
        "facets": facet_result_options,
        # find total submissions containing specified answer
        "total": facet_response['hits']['total'] - facet_response['facets'][field_name]['missing']
    }
    for facet in facet_response['facets'][field_name]['terms']:
        facet_result_options.append({
            "term": facet['term'],
            "count": facet['count']
        })
    return facet_result


def _create_facet_request_body(field_name, query_body):
    facet_terms = {"terms": {"field": field_name}}
    facet = {"facets": {field_name: facet_terms}}
    facet.update(query_body)
    return facet


def get_facets_for_choice_fields(dbm, form_model, search_parameters, local_time_delta):
    query_fields, search = _create_query(dbm, form_model, local_time_delta, search_parameters)
    query_body = search.to_dict()
    es = Elasticsearch(hosts=[{"host": ELASTIC_SEARCH_HOST, "port": ELASTIC_SEARCH_PORT}])
    total_submission_count = get_submission_count(dbm, form_model, search_parameters, local_time_delta)
    facet_results = []
    for field in form_model.choice_fields:
        field_name = es_questionnaire_field_name(field.code, form_model.id) + "_exact"
        facet = _create_facet_request_body(field_name, query_body)
        facet_response = es.search(index=dbm.database_name, doc_type=form_model.id, body=facet, search_type='count')
        facet_result = _get_facet_result(facet_response, field_name)
        facet_results.append(facet_result)

    return facet_results, total_submission_count


def get_all_submissions_ids_by_criteria(dbm, form_model, search_parameters, local_time_delta):
    total_submission_count = get_submission_count(dbm, form_model, search_parameters, local_time_delta)
    es = Elasticsearch(hosts=[{"host": ELASTIC_SEARCH_HOST, "port": ELASTIC_SEARCH_PORT}])
    query_fields, search = _create_query(dbm, form_model, local_time_delta, search_parameters)
    search = search.extra(size=total_submission_count, fields=[])
    body = search.to_dict()
    result = es.search(index=dbm.database_name, doc_type=form_model.id, body=body)
    return [entry['_id'] for entry in result['hits']['hits']]

