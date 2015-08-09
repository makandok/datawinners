from unittest import TestCase

from django.contrib.auth.models import User
from mock import Mock, patch

from mangrove.datastore.database import DatabaseManager
from datawinners.accountmanagement.models import NGOUserProfile
from datawinners.alldata.views import  get_project_info
from mangrove.form_model.project import Project


class TestViews(TestCase):
    def test_get_correct_web_submission_link(self):
        request = Mock()
        request.user = Mock(spec = User)
        manager = Mock(spec = DatabaseManager)
        manager.database = dict()
        raw_project = dict(_id = "pid", devices = ["sms", "web"],
                                        name = "Project Name",
                                        created = "2012-05-23T02:57:09.788294+00:00")

        project = Project(dbm=manager, name="Project Name")

        profile = Mock(spec = NGOUserProfile)

        questionnaire = Mock()
        questionnaire.form_code = "q01"

        with patch("datawinners.project.models.Project.get") as get_project:
            get_project.return_value = project
            with patch.object(DatabaseManager, "get") as db_manager:
                db_manager.return_value = questionnaire
                with patch("django.contrib.auth.models.User.get_profile") as get_profile:
                    get_profile.return_value = profile
                    profile.reporter = False
                    project_info = get_project_info(manager, raw_project)
                    self.assertEqual(project_info["web_submission_link"], "/project/testquestionnaire/pid/")

    def test_get_submission_link_if_poll_questionnaire(self):
        request = Mock()
        request.user = Mock(spec = User)
        manager = Mock(spec = DatabaseManager)
        manager.database = dict()
        raw_project = dict(_id = "pid", devices = ["sms", "web"],
                                        name = "Project Name",
                                        created = "2012-05-23T02:57:09.788294+00:00")

        project = Project(dbm=manager, name="Project Name", is_poll=True, form_code="q01")
        profile = Mock(spec = NGOUserProfile)

        questionnaire = Mock()
        questionnaire.form_code = "q01"

        with patch("datawinners.project.models.Project.get") as get_project:
            get_project.return_value = project
            with patch.object(DatabaseManager, "get") as db_manager:
                db_manager.return_value = questionnaire
                with patch("django.contrib.auth.models.User.get_profile") as get_profile:
                    get_profile.return_value = profile
                    profile.reporter = False
                    project_info = get_project_info(manager, raw_project)
                    self.assertEqual(project_info["link"], "/project/pid/results/q01/")
