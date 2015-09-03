import uuid
from nose.plugins.attrib import attr

from pages.adddatasenderspage.add_data_senders_page import AddDataSenderPage
from pages.alldatasenderspage.all_data_senders_page import AllDataSendersPage
from tests.addusertests.add_user_data import generate_user
from tests.testsettings import UI_TEST_TIMEOUT
from framework.base_test import HeadlessRunnerTest
from django.test import Client
from framework.utils.common_utils import by_xpath, by_css
from pages.loginpage.login_page import login
from testdata.test_data import DATA_WINNER_SMS_TESTER_PAGE, DATA_WINNER_USER_ACTIVITY_LOG_PAGE, LOGOUT, DATA_WINNER_ALL_DATA_SENDERS_PAGE, \
    DATA_WINNER_ALL_PROJECTS_PAGE
from tests.logintests.login_data import VALID_CREDENTIALS, PASSWORD
from pages.alluserspage.all_users_page import AllUsersPage
from tests.alluserstests.all_users_data import *
from pages.dashboardpage.dashboard_page import DashboardPage
from tests.projects.questionnairetests.project_questionnaire_data import SENDER, RECEIVER, SMS, VALID_SUMMARY_REPORT_DATA, QUESTIONNAIRE_CODE, \
    DEFAULT_QUESTION, QUESTION, GEN_RANDOM, CODE, TYPE, DATE, QUESTIONS, DATE_FORMAT, DD_MM_YYYY
from pages.smstesterpage.sms_tester_page import SMSTesterPage


QUESTIONNAIRE_DATA = {QUESTIONNAIRE_CODE: "addtest", GEN_RANDOM: True,
                      DEFAULT_QUESTION: {QUESTION: "What are you reporting on?", CODE: "q1"},
                      QUESTIONS: [{QUESTION: u"Date of report in DD.MM.YYY format", CODE: u"q3", TYPE: DATE,
                                   DATE_FORMAT: DD_MM_YYYY}]}

MESSAGE = 'message'

class TestAllUsers(HeadlessRunnerTest):

    def setUp(self):
        self.global_navigation = login(self.driver, VALID_CREDENTIALS)
        self.driver.go_to(ALL_USERS_URL)
        self.all_users_page = AllUsersPage(self.driver)

    def tearDown(self):
        self.global_navigation.sign_out()

    @attr('functional_test')
    def test_should_not_show_delete_if_any_users_selected(self):
        self.all_users_page.click_check_all_users(check=False)
        self.all_users_page.click_action_button()
        self.assertFalse(self.all_users_page.actions_menu_shown())

    @attr('functional_test')
    def test_should_not_delete_super_admin_user(self):
        self.assertFalse(self.all_users_page.is_editable('tester150411@gmail.com'))

    @attr('functional_test')
    def test_should_create_activity_log_and_submit_data(self):
        add_user_page = self.all_users_page.navigate_to_add_user()
        user_data = generate_user()
        add_user_page.select_role_as_administrator()
        add_user_page.add_user_with(user_data)
        add_user_page.get_success_message()
        self.global_navigation.sign_out()
        new_user_credential = {USERNAME: user_data[USERNAME], PASSWORD: "test123"}
        self.global_navigation = login(self.driver, new_user_credential)
        self.driver.go_to(DATA_WINNER_ALL_PROJECTS_PAGE)
        project_name, questionnaire_code = self.create_project()
        self.send_submission(user_data[MOBILE_PHONE], questionnaire_code)
        self.delete_user(user_data[USERNAME])
        self.check_sent_submission(project_name)
        self.check_deleted_user_name_on_activity_log_page(project_name)
        self.global_navigation.sign_out()
        self.global_navigation = login(self.driver, VALID_CREDENTIALS)

    @attr('functional_test')
    def test_should_update_user_name_when_edited_from_datasender_page(self):
        add_user_page = self.all_users_page.navigate_to_add_user()
        add_user_page.select_role_as_administrator()
        add_user_page.add_user_with(EDIT_USER_DATA)
        add_user_page.get_success_message()
        self.driver.go_to(DATA_WINNER_ALL_DATA_SENDERS_PAGE)
        all_datasenders_page = AllDataSendersPage(self.driver)
        all_datasenders_page.search_with(EDIT_USER_DATA.get('username'))
        self.driver.find(all_datasenders_page.get_checkbox_selector_for_datasender_row(1)).click()
        all_datasenders_page.select_edit_action()
        EDIT_DETAILS = {"name": "New testUser",
                        "mobile_number": EDIT_USER_DATA.get("mobile_phone"),
                        "commune": "Madagascar",
                        "gps": "-21.7622088847 48.0690991394"}
        AddDataSenderPage(self.driver).enter_data_sender_details_from(EDIT_DETAILS).navigate_to_datasender_page()
        self.driver.go_to(ALL_USERS_URL)
        self.all_users_page = AllUsersPage(self.driver)
        user_name = self.all_users_page.get_full_name_for(EDIT_USER_DATA.get("username"))
        self.assertEquals(EDIT_DETAILS.get("name"), user_name)

    def send_submission(self, mobile_number, questionnaire_code):
        client = Client()
        valid_sms = {"from_msisdn": mobile_number,
                     "to_msisdn": '919880734937',
                     MESSAGE: "%s 10.10.2010" % questionnaire_code,
                     "message_id": uuid.uuid1().hex}
        resp = client.post('/submission', valid_sms)
        self.assertIn("Thank you", resp.content)

    def create_project(self):
        dashboard_page = DashboardPage(self.driver)
        create_project_page = dashboard_page.navigate_to_create_project_page()
        create_project_page = create_project_page.select_blank_questionnaire_creation_option()
        create_project_page.create_questionnaire_with(VALID_SUMMARY_REPORT_DATA, QUESTIONNAIRE_DATA)
        overview_page = create_project_page.save_and_create_project_successfully()
        questionnaire_code = overview_page.get_questionnaire_code()
        project_name = overview_page.get_project_title()
        return project_name, questionnaire_code

    def delete_user(self, username):
        self.global_navigation.sign_out()
        login(self.driver, VALID_CREDENTIALS)
        self.driver.go_to(ALL_USERS_URL)
        all_users_page = AllUsersPage(self.driver)
        self.driver.find(by_xpath("//td[contains(.,'%s')]/../td/input" % username)).click()
        all_users_page.select_delete_action(confirm=True)
        self.driver.wait_for_element(UI_TEST_TIMEOUT, by_css("span.loading"), True)
        self.driver.wait_until_modal_dismissed()
        message = all_users_page.get_message()
        self.assertEqual(message, SUCCESSFULLY_DELETED_USER_MSG)

    def check_sent_submission(self, project_name):
        all_data_page = self.global_navigation.navigate_to_all_data_page()
        data_analysis_page = all_data_page.navigate_to_data_analysis_page(project_name)
        data_sender_name = data_analysis_page.get_all_data_on_nth_row(1)[1]
        self.assertTrue("Mino" in data_sender_name)

    def check_deleted_user_name_on_activity_log_page(self, project_name):
        self.driver.go_to(DATA_WINNER_USER_ACTIVITY_LOG_PAGE)
        username = self.driver.find(by_xpath("//td[contains(.,'%s')]/../td[1]" % project_name)).text
        action = self.driver.find(by_xpath("//td[contains(.,'%s')]/../td[2]" % project_name)).text
        self.assertEqual("Deleted User", username)
        self.assertEqual("Created Questionnaire", action)

    @attr('functional_test')
    def test_should_check_if_org_settings_is_restricted_to_extended_user(self):
        add_user_page = self.all_users_page.navigate_to_add_user()
        add_user_page.select_role_as_administrator()
        user_data = generate_user()
        add_user_page.add_user_with(user_data)
        add_user_page.get_success_message()
        self.global_navigation.sign_out()
        new_user_credential = {USERNAME: user_data[USERNAME], PASSWORD: "test123"}
        login(self.driver, new_user_credential)
        self.driver.go_to(ORG_SETTINGS_URL)
        title = self.driver.get_title()
        self.assertEqual(title, ACCESS_DENIED_TITLE)

    @attr('functional_test')
    def test_should_check_if_account_settings_is_restricted_to_project_manager(self):
        add_user_page = self.all_users_page.navigate_to_add_user()
        add_user_page.select_role_as_project_manager()
        add_user_page.select_questionnaires(2)
        new_user_data = generate_user()
        add_user_page.add_user_with(new_user_data)
        add_user_page.get_success_message()
        self.global_navigation.sign_out()
        new_user_credential = {USERNAME: new_user_data[USERNAME], PASSWORD: "test123"}
        login(self.driver, new_user_credential)
        self.driver.go_to(ORG_SETTINGS_URL)
        title = self.driver.get_title()
        self.assertEqual(title, ACCESS_DENIED_TITLE)
        self.driver.go_to(ALL_USERS_URL)
        title = self.driver.get_title()
        self.assertEqual(title, ACCESS_DENIED_TITLE)

