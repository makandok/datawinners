import elasticutils
from datawinners.main.database import get_db_manager
from datawinners.search.mapping import form_model_change_handler
from datawinners.search.submission_index import create_submission_mapping
from datawinners.settings import ELASTIC_SEARCH_URL
from mangrove.form_model.form_model import get_form_model_by_code
from datawinners.search.subject_index import entity_search_update, create_subject_mapping
from mangrove.datastore.documents import EntityDocument, FormModelDocument, EnrichedSurveyResponseDocument

from datawinners.project.models import Project
from datawinners.search.datasender_index import update_datasender_for_project_change, create_ds_mapping


def update_submission_search_index(submission_doc,feed_dbm):
    es = elasticutils.get_es(urls=ELASTIC_SEARCH_URL)
    dbm = get_db_manager(feed_dbm.database_name.replace("feed_",""))
    form_model = get_form_model_by_code(dbm, submission_doc.form_code)
    search_dict = {}
    search_dict.update({"status": submission_doc.status})
    search_dict.update({"date": submission_doc.survey_response_modified_time.strftime("%b. %d,%Y, %H:%M %p")})
    search_dict.update({"ds_id": submission_doc.data_sender.get('id')})
    search_dict.update({"ds_name": submission_doc.data_sender.get('last_name')})
    search_dict.update({"error_msg":submission_doc.error_message})
    for key in submission_doc.values:
        field = submission_doc.values[key]
        if submission_doc.status == 'error':
            value = field
        else:
            value = field.get("answer")
        if (isinstance(value,dict)):
            if field.get('is_entity_question'):
                value = value.get("name")
            else:
                value = ','.join(value.values())
        search_dict.update({key: value})
    es.index(dbm.database_name, form_model.id, search_dict, id=submission_doc.id)


EntityDocument.register_post_update(entity_search_update)

FormModelDocument.register_post_update(form_model_change_handler)
Project.register_post_update(update_datasender_for_project_change)

EnrichedSurveyResponseDocument.register_post_update(update_submission_search_index)
