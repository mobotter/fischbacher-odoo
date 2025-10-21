from odoo import fields
from odoo.tests.common import TransactionCase
from odoo import models


class TestTrigger(models.Model):
    _inherit = "method_hook.trigger.mixin"
    _name = "test.method_hook.test_trigger"
    _description = "Test method hook Trigger"

    def _trigger(self, instance, args, method_name):
        breakpoint()


class TestModel(models.Model):
    _name = "test.method_hook.test_trigger.partner"
    _description = "Test Model Method Hooks"
    name = fields.Char("Name")


class TestTrigger(TransactionCase):
    def setUp(self):
        super().setUp()
        self.partner = self.env["res.partner"].create({"name": "trigger"})

    def test_trigger(self):
        self.env["test.method_hook.test_trigger"].create(
            {
                "model_id": self.env.ref(
                    "method_trigger.model_test_method_hook_test_trigger_partner"
                ).id,
                "method": "write",
                "link_expression": "object",
                "domain": [("id", ">", 0)],
            }
        )
        partner = self.env[TestModel._name].create({"name": "triggermodel1"})
        partner.write({"name": "123"})
