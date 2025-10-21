from odoo import _, api, fields, models, SUPERUSER_ID
from odoo.exceptions import UserError, RedirectWarning, ValidationError


class MailActivity(models.Model):
    _inherit = "mail.activity"

    def unlink(self):
        self._set_flow_items_as_done()
        return super().unlink()

    def _set_flow_items_as_done(self):
        for rec in self:
            flow_item = (
                rec.env["of.instance.item"]
                .sudo()
                .search([("mail_activity_id", "=", rec.id)])
            )
            if not flow_item:
                continue
            flow_item.mail_activity_done = True
            flow_item._heartbeat()
