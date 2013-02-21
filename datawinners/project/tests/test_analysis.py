import unittest
from mock import patch, PropertyMock
from mangrove.datastore.database import DatabaseManager
from mangrove.form_model.form_model import FormModel
from mangrove.transport.submissions import Submission
from project.analysis import Analysis

class TestAnalysis(unittest.TestCase):
    def setUp(self):
        self.form_model = PropertyMock(return_value=FormModel)
        self.manager = PropertyMock(return_value=DatabaseManager)
        self.filters = {u"name": "abcd"}

    def test_should_return_leading_part_of_submissions(self):
        with patch("datawinners.project.submission_data.SubmissionData._get_submissions_by_type") as get_submissions:
            with patch("datawinners.project.submission_data.SubmissionData._get_submission_details") as get_submission_details:
                get_submissions.return_value = [Submission(self.manager,form_code="cli001", values={"eid": "cli14", "RD": "01.01.2012", "SY": "a2bc", "BG": "d"})]
                get_submission_details.return_value = ('Tester Pune', 'admin', 'tester150411@gmail.com'), "12-03-2012", ('Clinic-One', u'cli15'), "23-02-2012"
                analysis_data = Analysis(self.form_model, self.manager, "org_id", self.filters)
                leading_part = analysis_data._get_leading_part_for_excel()
                expected_leading_part = [['Clinic-One', u'cli15', "12-03-2012","23-02-2012", "Tester Pune", "admin"]]
                self.assertEqual(expected_leading_part,leading_part)

#    def test_should_populate_excel_data(self):
#        with patch("datawinners.project.submission_data.SubmissionData._get_submissions_by_type") as get_submissions:
#            with patch(
#                "datawinners.project.submission_data.SubmissionData._get_submission_details") as get_submission_details:
#                get_submissions.return_value = [Submission(self.manager, form_code="cli001",
#                                                           values={"eid": "cli14", "RD": "01.01.2012", "SY": "a2bc",
#                                                                   "BG": "d"})]
#                get_submission_details.return_value = (
#                                                          'Tester Pune', 'admin', 'tester150411@gmail.com'), "12-03-2012", (
#                                                          'Clinic-One', u'cli15'), "23-02-2012"
#                analysis_data = Analysis(self.form_model, self.manager, "org_id", self.filters)
#                analysis_data._init_excel_values()
