import logging
from datawinners.accountmanagement.models import Organization


class ExceptionMiddleware(object):
    def __init__(self):
        self.logger = logging.getLogger('datawinners')

    def process_exception(self, request, exception):
        try:
            request.META['user_email_id'] = request.user.username
            profile = request.user.get_profile()
            organization = Organization.objects.get(org_id=profile.org_id)
            request.META['organization_details'] = ('%s (%s)' % (organization.name, profile.org_id))
            self.logger.exception("Exception happened for request "+request.path)
        except Exception as ex:
            self.logger.error("Failed to get customer data for: %s", request.user.username)
            self.logger.error("error while getting meta info to be provided via email", ex)
        return None

