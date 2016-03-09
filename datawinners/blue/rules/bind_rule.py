from mangrove.form_model.xform import add_attrib

from datawinners.blue.rules.rule import Rule


class ConstraintMessageRule(Rule):
    def edit(self, node, old_field, new_field, xform):
        bind_node = xform.bind_node(node)
        if bind_node is not None and new_field.constraint_message != old_field.constraint_message:
            add_attrib(bind_node, 'constraintMsg', new_field.constraint_message)

    def change_mapping(self):
        return False

    def update_submission(self, submission):
        return False

    def remove(self, parent_node, node, xform):
        pass
