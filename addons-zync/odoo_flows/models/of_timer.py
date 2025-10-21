import arrow
from odoo import _, api, fields, models, SUPERUSER_ID
from odoo.exceptions import UserError, RedirectWarning, ValidationError
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DTF


class Timer(models.Model):
    _inherit = ["of.base.item.abstract"]
    _inherits = {"of.base.item": "item_id"}
    _name = "of.timer"
    _description = "Flows Timer"

    interval_number = fields.Integer(default=1)
    interval_type = fields.Selection(
        [
            ("seconds", "Seconds"),
            ("minutes", "Minutes"),
            ("hours", "Hours"),
            ("days", "Days"),
            ("weeks", "Weeks"),
            ("months", "Months"),
        ],
        string="Interval Unit",
        default="days",
        required=True,
    )

    def _get_deadline(self, instance_item):
        date = arrow.get(instance_item.date_started.strftime(DTF))
        params = {
            self.interval_type: self.interval_number,
        }
        deadline = date.shift(**params)
        return deadline

    def _heartbeat(self, instance_item, additional_data):
        super()._heartbeat(instance_item, additional_data)

        deadline = self._get_deadline(instance_item)

        if arrow.utcnow() < deadline:
            return

        instance_item._goto_next()
