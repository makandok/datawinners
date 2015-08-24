# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
from django.contrib.auth.models import User
from framework.exception import CouldNotLocateElementException
from pages.edituserpage.edit_user_page import EditUserPage

from pages.page import Page
from framework.utils.data_fetcher import from_, fetch_
from pages.alluserspage.all_users_locator import *
from tests.alluserstests.all_users_data import DELETE, EDIT
from framework.utils.common_utils import by_css
from pages.adduserpage.add_user_page import AddUserPage


class AllUsersPage(Page):
    def __init__(self, driver):
        Page.__init__(self, driver)

    def click_check_all_users(self, check=True):
        checkbox = self.driver.find(CHECK_ALL_USERS_LOCATOR)
        if (checkbox.get_attribute("checked") != "true" and check) or \
                (checkbox.get_attribute("checked") == "true" and not check):
            checkbox.click()

    def select_delete_action(self, confirm=False, cancel=False):
        action_to_be_performed = DELETE
        self.perform_user_action(action_to_be_performed)
        if confirm:
            self.confirm_delete()
        if cancel:
            self.cancel_delete()

    def select_edit_action(self, confirm=False, cancel=False):
        action_to_be_performed = EDIT
        self.perform_user_action(action_to_be_performed)
        return EditUserPage(self.driver)

    def perform_user_action(self, action_to_be_performed):
        self.click_action_button()
        option = self.driver.find_visible_element(by_id(action_to_be_performed))
        option.click()

    def check_nth_user(self, number):
        self.driver.find(by_css(CHECK_NTH_USER_LOCATOR % str(number))).click()

    def get_error_message(self):
        if self.driver.is_element_present(ERROR_CONTAINER):
            return self.driver.find(ERROR_CONTAINER).text
        return False

    def confirm_delete(self):
        self.driver.find(CONFIRM_DELETE_BUTTON).click()

    def cancel_delete(self):
        self.driver.find(CANCEL_DELETE_BUTTON).click()

    def get_message(self):
        if self.driver.is_element_present(MESSAGES_CONTAINER):
            return self.driver.find(MESSAGES_CONTAINER).text
        return False

    def navigate_to_add_user(self):
        self.driver.find(ADD_USER_LINK).click()
        return AddUserPage(self.driver)

    def actions_menu_shown(self):
        return self.driver.find(ACTION_MENU).is_displayed()

    def click_action_button(self):
        self.driver.find(ALL_USERS_ACTION_SELECT).click()

    def check_user_by_username(self, username):
        user_id = User.objects.get(username=username).id
        self.driver.find_element_by_css_selector('input[value="%s"]' % user_id).click()

    def get_questionnaire_list_for(self, username):
        return self.driver.find(
            by_xpath("//*[@id='users_list']//tr/td[contains(text(), '%s')]/../td[4]" % username)).text.split("\n")

    def get_role_for(self, username):
        return self.driver.find(
            by_xpath("//*[@id='users_list']//tr/td[contains(text(), '%s')]/../td[3]" % username)).text

    def select_user_with_username(self, username):
        self.driver.find(
            by_xpath("//*[@id='users_list']//tr/td[contains(text(), '%s')]/../td[1]/input" % username)).click()

    def is_editable(self, username):
        try:
            self.driver.find(by_xpath("//*[@id='users_list']//tr/td[contains(text(), '%s')]/../td[1]/input" % username))
            return True
        except CouldNotLocateElementException:
            return False

    def get_full_name_for(self, username):
        return self.driver.find(
            by_xpath("//*[@id='users_list']//tr/td[contains(text(), '%s')]/../td[2]" % username)).text

    def number_of_editable_users_for_role(self, role):
        elements_by_xpath = self.driver.find_elements_by_xpath(
            "//*[@id='users_list']//tr/td[contains(text(), '%s')]/../td[1]/input" % role)
        return len(elements_by_xpath)
