from framework.utils.common_utils import random_number, random_string

def generate_user():
    return {
        TITLE: "Developer",
        NAME: "Mino Rakoto",
        USERNAME: random_string(7)+"@mailinator.com",
        MOBILE_PHONE: random_number(9)
    }

TITLE = "title"
NAME = "full_name"
USERNAME = "username"
MOBILE_PHONE = "mobile_phone"
ADDED_USER_SUCCESS_MSG = u'User has been added successfully'
DASHBOARD_PAGE_TITLE = u'Dashboard'
DEFAULT_PASSWORD = "test123"