# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
import os
import uuid

from nose.plugins.attrib import attr
import requests

from framework.base_test import HeadlessRunnerTest
from framework.utils.common_utils import by_css
from framework.utils.data_fetcher import fetch_, from_
from pages.adddatasenderspage.add_data_senders_page import AddDataSenderPage
from pages.alldatapage.all_data_page import AllDataPage
from pages.alldatasenderspage.all_data_senders_page import AllDataSendersPage
from pages.allsubjectspage.add_subject_page import AddSubjectPage
from pages.allsubjectspage.all_subjects_list_page import AllSubjectsListPage
from pages.dashboardpage.dashboard_page import DashboardPage
from pages.loginpage.login_page import login
from pages.projectoverviewpage.project_overview_page import ProjectOverviewPage
from pages.submissionlogpage.submission_log_locator import DELETE_BUTTON
from pages.submissionlogpage.submission_log_page import SubmissionLogPage, MONTHLY_DATE_RANGE
from testdata.test_data import DATA_WINNER_ALL_DATA_SENDERS_PAGE, ALL_DATA_PAGE, DATA_WINNER_SMS_TESTER_PAGE, \
    DATA_WINNER_DASHBOARD_PAGE, \
    url
from tests.dataanalysistests.data_analysis_data import DAILY_DATE_RANGE, CURRENT_MONTH, LAST_MONTH, YEAR_TO_DATE
from tests.submissionlogtests.submission_log_data import *
from pages.warningdialog.warning_dialog import WarningDialog
from tests.testsettings import UI_TEST_TIMEOUT
from tests.utils import get_subject_short_code
from testdata.test_data import LOGOUT


SUBMISSION_DATE_FORMAT_FOR_SUBMISSION_LOG = "%b. %d, %Y, %H:%M"


def send_sms_with(sms):
    data = {"message": sms[SMS], "from_msisdn": sms[SENDER], "to_msisdn": sms[RECEIVER], "message_id": uuid.uuid1().hex}
    resp = requests.post(url("/") + "submission", data)
    return resp.content


def send_valid_sms_with(sms):
    response = send_sms_with(sms)
    assert "Thank" in response, " Thank not found in response [%s]" % response


class TestSubmissionLog(HeadlessRunnerTest):
    def setUp(self):
        self.dashboard = login(self.driver)
        self.reporting_period_project_name = None
        self.URL = None

    def tearDown(self):
        self.driver.go_to(LOGOUT)


    def _create_project(self, project_data, questionnaire_data, monthly):
        self.driver.go_to(DATA_WINNER_DASHBOARD_PAGE)
        self.dashboard_page = DashboardPage(self.driver)
        create_questionnaire_options_page = self.dashboard_page.navigate_to_create_project_page()
        create_questionnaire_page = create_questionnaire_options_page.select_blank_questionnaire_creation_option()
        create_questionnaire_page.create_questionnaire_with(project_data, questionnaire_data)
        if monthly:
            create_questionnaire_page.select_question_link(1)
            create_questionnaire_page.change_date_type_question(date_format=MM_YYYY)
        create_questionnaire_page.save_and_create_project_successfully()

    def populate_data_for_date_range_filters(self, project_data=NEW_PROJECT_DATA,
                                             questionnaire_data=DATE_PROJECT_QUESTIONNAIRE_DATA, monthly=False):
        self._create_project(project_data, questionnaire_data, monthly)
        project_name, questionnaire_code = self._get_project_details()
        self.driver.go_to(DATA_WINNER_ALL_DATA_SENDERS_PAGE)
        all_datasenders_page = AllDataSendersPage(self.driver)
        all_datasenders_page.associate_datasender_to_projects("rep11", [project_name.lower()])
        self._submit_sms_data(questionnaire_code, monthly=monthly)
        return project_name

    def _get_project_details(self):
        overview_page = ProjectOverviewPage(self.driver)
        return overview_page.get_project_title(), overview_page.get_questionnaire_code()

    def _submit_sms_data(self, questionnaire_code, monthly):
        dates = get_reporting_date_values(monthly)
        for i in dates:
            send_valid_sms_with(get_sms_data_with_questionnaire_code(questionnaire_code, i))


    def get_first_project_submission_log_page(self):
        if self.URL:
            self.driver.go_to(self.URL)
            submission_log_page = SubmissionLogPage(self.driver)
        else:
            submission_log_page = self.go_to_submission_log_page()
            if not self.URL:
                self.URL = self.driver.current_url
        return submission_log_page

    def go_to_submission_log_page(self, project_name=FIRST_PROJECT_NAME):
        self.driver.go_to(ALL_DATA_PAGE)
        submission_log_page = AllDataPage(self.driver).navigate_to_submission_log_page(project_name)
        return submission_log_page

    def assert_none_selected_shown(self, submission_log_page):
        self.assertTrue(submission_log_page.is_none_selected_shown())
        self.assertFalse(submission_log_page.actions_menu_shown())

    def assert_action_menu_shown_for(self, submission_log_page):
        self.assertTrue(submission_log_page.actions_menu_shown())
        self.assertFalse(submission_log_page.is_none_selected_shown())

    def register_datasender(self, datasender_details, all_datasenders_page, id=None):
        add_data_sender_page = all_datasenders_page.navigate_to_add_a_data_sender_page()
        add_data_sender_page.enter_data_sender_details_from(datasender_details, unique_id=id)
        return add_data_sender_page.get_rep_id_from_success_message(
            add_data_sender_page.get_success_message()) if id is None else id


    @attr("functional_test")
    def test_should_update_submission_log_when_DS_info_is_edited(self):
        all_project_page = self.dashboard.navigate_to_view_all_project_page()
        project_overview_page = all_project_page.navigate_to_project_overview_page("clinic test project1")
        my_data_sender_page = project_overview_page.navigate_to_datasenders_page()
        add_ds_page = my_data_sender_page.navigate_to_add_a_data_sender_page()
        add_ds_page.enter_data_sender_details_from(DATASENDER_DETAILS)
        ds_id = add_ds_page.get_rep_id_from_success_message(add_ds_page.get_success_message())

        send_valid_sms_with(VALID_DATA)

        submission_log_page = self.get_first_project_submission_log_page()
        submission_log_page.search(ds_id)
        self.assertTrue(DATASENDER_DETAILS[NAME] in submission_log_page.get_cell_value(row=1, column=2))

        self.driver.go_to(DATA_WINNER_ALL_DATA_SENDERS_PAGE)
        all_datasenders_page = AllDataSendersPage(self.driver)

        all_datasenders_page.search_with(ds_id)
        all_datasenders_page.wait_for_table_to_load()

        all_datasenders_page.select_a_data_sender_by_id(ds_id)
        all_datasenders_page.select_edit_action()
        AddDataSenderPage(self.driver).enter_data_sender_details_from(EDITED_DATASENDER_DETAILS)
        submission_log_page = self.get_first_project_submission_log_page()
        submission_log_page.search(ds_id)
        self.assertTrue(EDITED_DATASENDER_DETAILS[NAME] in submission_log_page.get_cell_value(row=1, column=2))

    @attr("functional_test")
    def test_should_update_submission_log_when_subject_info_is_edited(self):
        self.driver.go_to(url("/entity/subject/create/clinic/?web_view=True&"))
        add_subject_page = AddSubjectPage(self.driver)
        add_subject_page.add_subject_with(VALID_DATA_FOR_SUBJECT)
        add_subject_page.submit_subject()
        message = fetch_(SUCCESS_MESSAGE, from_(VALID_DATA_FOR_SUBJECT))

        flash_message = add_subject_page.get_flash_message()
        subject_short_code = get_subject_short_code(flash_message)
        message = message % subject_short_code
        self.assertIn(message, flash_message)

        VALID_SMS_FOR_EDIT_SUBJECT[SMS] = VALID_SMS_FOR_EDIT_SUBJECT[SMS].replace('short_code', subject_short_code, 1)
        send_valid_sms_with(VALID_SMS_FOR_EDIT_SUBJECT)

        submission_log_page = self.get_first_project_submission_log_page()
        submission_log_page.search(subject_short_code)
        self.assertIn(fetch_(SUB_LAST_NAME, VALID_DATA_FOR_SUBJECT), submission_log_page.get_cell_value(1, 5))

        self.driver.go_to(url("/entity/subjects/clinic/"))
        subject_list_page = AllSubjectsListPage(self.driver)
        self.driver.wait_for_page_load()
        subject_list_page.select_subject_by_id(subject_short_code)
        edit_subject_page = subject_list_page.click_edit_action_button()
        edit_subject_page.add_subject_with(VALID_DATA_FOR_EDIT)
        edit_subject_page.submit_subject()

        submission_log_page = self.get_first_project_submission_log_page()
        submission_log_page.search(subject_short_code)
        self.assertIn(fetch_(SUB_LAST_NAME, VALID_DATA_FOR_EDIT), submission_log_page.get_cell_value(1, 5))


    def make_web_submission(self, project_name, submission):
        all_data_page = self.dashboard.navigate_to_all_data_page()
        web_submission_page = all_data_page.navigate_to_web_submission_page(project_name)
        self.driver.wait_for_page_with_title(5, web_submission_page.get_title())
        web_submission_page.fill_questionnaire_with(submission)
        web_submission_page.submit_answers()

    @attr("functional_test")
    def test_should_filter_by_name_and_id_of_datasender_and_subject(self):

        self.driver.go_to(DATA_WINNER_SMS_TESTER_PAGE)
        send_valid_sms_with(SMS_REGISTER_SUBJECT)
        send_valid_sms_with(SMS_WEB_SUBMISSION)

        submission_log_page = self.go_to_submission_log_page()
        submission_log_page.wait_for_table_data_to_load()

        datasender_name = 'Tester'
        submission_log_page.filter_by_datasender(datasender_name)
        submission_log_page.wait_for_table_data_to_load()
        self._verify_filtered_records_by_datasender_name_or_id(datasender_name, submission_log_page)

        project_name = fetch_("last_name", from_(SUBJECT_DATA))
        submission_log_page.filter_by_subject(project_name)
        submission_log_page.wait_for_table_data_to_load()
        self._verify_filtered_records_by_subject_name_or_id(project_name, submission_log_page)

        datasender_id = 'rep276'
        submission_log_page.refresh()
        submission_log_page.filter_by_datasender(datasender_id)
        submission_log_page.wait_for_table_data_to_load()
        self._verify_filtered_records_by_datasender_name_or_id(datasender_id, submission_log_page)

        project_short_code = fetch_("short_code", from_(SUBJECT_DATA))
        submission_log_page.refresh()
        submission_log_page.filter_by_subject(project_short_code)
        submission_log_page.wait_for_table_data_to_load()
        self._verify_filtered_records_by_subject_name_or_id(project_short_code, submission_log_page)

    def _verify_filtered_records_by_datasender_name_or_id(self, datasender, submission_log_page):
        total_number_of_rows = submission_log_page.get_total_number_of_rows()
        for i in range(1, total_number_of_rows):
            self.assertIn(datasender, submission_log_page.get_cell_value(i, 2))

    def _verify_filtered_records_by_subject_name_or_id(self, project, submission_log_page):
        total_number_of_rows = submission_log_page.get_total_number_of_records()
        for i in range(1, total_number_of_rows):
            self.assertIn(project, submission_log_page.get_cell_value(i, 5))

    def assert_reporting_period_values(self, submission_log_page, total_number_of_rows, monthly=False):
        rp_column = 6
        all_reporting_dates = []
        dates = get_reporting_date_values(monthly)
        for i in range(1, total_number_of_rows + 1):
            all_reporting_dates.append(submission_log_page.get_cell_value(i, rp_column))
        self.assertTrue(set(all_reporting_dates).issubset(dates))

    @attr("functional_test")
    def test_date_filters(self):
        if not self.reporting_period_project_name:
            self.reporting_period_project_name = self.populate_data_for_date_range_filters()

        submission_log_page = self.go_to_submission_log_page(project_name=self.reporting_period_project_name)

        submission_log_page.filter_by_submission_date(DAILY_DATE_RANGE)

        submission_log_page.wait_for_table_data_to_load()
        total_number_of_rows = submission_log_page.get_total_number_of_records()
        self.assertEqual(total_number_of_rows, 4)

        submission_log_page.filter_by_submission_date(LAST_MONTH)

        submission_log_page.wait_for_table_data_to_load()
        total_number_of_rows = submission_log_page.get_total_number_of_records()
        self.assertEqual(total_number_of_rows, 0)
        self.assertEqual('No matching records found', submission_log_page.get_empty_datatable_text())

        submission_log_page.filter_by_submission_date(YEAR_TO_DATE)

        submission_log_page.wait_for_table_data_to_load()
        total_number_of_rows = submission_log_page.get_total_number_of_records()
        self.assertEqual(total_number_of_rows, 4)

        # submission_log_page.filter_by_reporting_date(DAILY_DATE_RANGE)

        #submission_log_page.wait_for_table_data_to_load()
        #total_number_of_rows = submission_log_page.get_total_number_of_records()
        #self.assertEqual(total_number_of_rows, 1)
        #self.assert_reporting_period_values(submission_log_page, total_number_of_rows)
        #
        #submission_log_page.filter_by_reporting_date(CURRENT_MONTH)
        #
        #submission_log_page.wait_for_table_data_to_load()
        #total_number_of_rows = submission_log_page.get_total_number_of_records()
        #self.assertEqual(total_number_of_rows, 2)
        #self.assert_reporting_period_values(submission_log_page, total_number_of_rows)
        #
        #submission_log_page.filter_by_reporting_date(LAST_MONTH)
        #
        #submission_log_page.wait_for_table_data_to_load()
        #total_number_of_rows = submission_log_page.get_total_number_of_records()
        #self.assertEqual(total_number_of_rows, 1)
        #self.assert_reporting_period_values(submission_log_page, total_number_of_rows)
        #
        #submission_log_page.filter_by_reporting_date(YEAR_TO_DATE)
        #
        #now = datetime.now()
        #year_to_date_expected = len([d for d in get_reporting_date_values(False) if
        #                             datetime.strptime(d, "%d.%m.%Y").year == now.year and datetime.strptime(d,
        #                                                                                                     "%d.%m.%Y") <= now])
        #submission_log_page.wait_for_table_data_to_load()
        #total_number_of_rows = submission_log_page.get_total_number_of_records()
        #self.assertEqual(total_number_of_rows, year_to_date_expected)
        #self.assert_reporting_period_values(submission_log_page, total_number_of_rows)
        #
        #submission_log_page.filter_by_reporting_date(ALL_PERIODS)

        #self.assert_reporting_period_values(submission_log_page, total_number_of_rows)

        #self.assert_reporting_period_values(submission_log_page, total_number_of_rows)


    def verify_sort_data_by_date(self, submission_log_page, column, sort_predicate,
                                 date_format=SUBMISSION_DATE_FORMAT_FOR_SUBMISSION_LOG):
        date_strings = submission_log_page.get_all_data_on_nth_column(column)
        self.assertTrue(len(date_strings) >= 3)
        dates = []
        for date in date_strings:
            dates.append(datetime.strptime(date, date_format))

        self.assertTrue(sort_predicate(dates[0], dates[1]), msg="Dates:" + str(dates))
        self.assertTrue(sort_predicate(dates[1], dates[2]), msg="Dates:" + str(dates))

    @attr('functional_test')
    def test_sorting_on_date_columns(self):
        if not self.reporting_period_project_name:
            self.reporting_period_project_name = self.populate_data_for_date_range_filters()
        submission_log_page = self.go_to_submission_log_page(project_name=self.reporting_period_project_name)
        submission_log_page.wait_for_table_data_to_load()
        # default sorting on submission date should be in descending order
        self.verify_sort_data_by_date(submission_log_page, 3, greater_than_equal)
        submission_log_page.click_on_nth_header(5)
        submission_log_page.wait_for_table_data_to_load()
        self.verify_sort_data_by_date(submission_log_page, 5, less_than_equal, date_format='%d.%m.%Y')

    @attr('functional_test')
    def test_should_delete_submission(self):
        send_valid_sms_with(VALID_DATA_FOR_DELETE)

        submission_log_page = self.go_to_submission_log_page()
        submission_log_page.search(unique_text)
        submission_log_page.wait_for_table_data_to_load()

        submission_log_page.check_submission_by_row_number(1)
        submission_log_page.choose_on_dropdown_action(DELETE_BUTTON)
        warning_dialog = WarningDialog(self.driver)
        warning_dialog.confirm()
        self.driver.wait_for_element(UI_TEST_TIMEOUT, by_css('#message_text .success-box'))
        delete_success_text = self.driver.find_visible_element(by_css('#message_text')).text
        self.assertEqual(delete_success_text, "The selected submissions have been deleted")
        submission_log_page.wait_for_table_data_to_load()
        self.assertEquals(int(submission_log_page.get_total_number_of_records()), 0)


def less_than_equal(x, y):
    return x <= y


def greater_than_equal(x, y):
    return x >= y

