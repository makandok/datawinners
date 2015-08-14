# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
from registration.signals import user_registered, user_activated
from datawinners.accountmanagement.post_registration_events import ngo_user_created
from datawinners.accountmanagement.post_activation_events import initialize_organization

import user
user_registered.connect(ngo_user_created)
user_activated.connect(initialize_organization)
