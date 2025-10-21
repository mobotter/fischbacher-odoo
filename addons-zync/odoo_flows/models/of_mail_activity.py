import arrow
from odoo import _, api, fields, models, SUPERUSER_ID
from odoo.exceptions import UserError, RedirectWarning, ValidationError
from odoo.tools.safe_eval import safe_eval


class MailActivity(models.Model):
    _inherits = {"of.base.item": "item_id"}
    _inherit = ["of.base.item.abstract"]
    _name = "of.mail_activity"
    _description = "Flows Mail Activity"

    activity_type_id = fields.Many2one(
        "mail.activity.type", string="Activity Type", ondelete="restrict"
    )
    summary = fields.Text("Summary")
    due_days = fields.Integer("Due Days")
    user_id = fields.Many2one("res.users", string="Assignee")

    def _heartbeat(self, instance_item, additional_data):
        self.ensure_one()

        super()._heartbeat(instance_item, additional_data)

        if (
            not instance_item.mail_activity_id
            and not instance_item.mail_activity_created
        ):
            self._make_activity(instance_item)
        elif not instance_item.mail_activity_id and instance_item.mail_activity_done:
            # done:
            instance_item._goto_next()

    def _make_activity(self, instance_item):
        model = self.env["ir.model"].search([("model", "=", instance_item.model)])
        model.ensure_one()

        dt = arrow.utcnow().shift(days=self.due_days).datetime

        data = {
            "activity_type_id": self.activity_type_id.id,
            "res_model_id": model.id,
            "res_id": instance_item.res_id,
            "automated": True,
            "date_deadline": fields.Datetime.to_string(dt),
            "summary": self.summary,
        }
        if self.user_id:
            data["user_id"] = self.user_id.id
        instance_item.mail_activity_id = self.env["mail.activity"].create(data)
        instance_item.mail_activity_created = True
