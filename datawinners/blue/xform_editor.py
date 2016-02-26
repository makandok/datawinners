from datawinners.blue.rules import REGISTERED_RULES


class UnsupportedXformEditException(Exception):
    def __init__(self):
        self.message = "Unsupported xlsform edit exception"

class XFormEditor(object):
    def edit(self, new_questionnaire, old_questionnaire):
        if not self._validate(new_questionnaire, old_questionnaire):
            raise UnsupportedXformEditException()
        # questionnaire.save(process_post_update=False)

    def _validate(self, new_questionnaire, old_questionnaire):
        for rule in REGISTERED_RULES:
            rule.update_xform(old_questionnaire, new_questionnaire)

        return old_questionnaire.xform == new_questionnaire.xform

    def _apply(self):
        pass
