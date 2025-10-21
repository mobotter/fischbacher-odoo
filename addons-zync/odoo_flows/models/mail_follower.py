from odoo import _, api, fields, models, SUPERUSER_ID
from odoo.exceptions import UserError, RedirectWarning, ValidationError


class MailFollower(models.Model):
    _inherit = "mail.followers"

    def _get_recipient_data(self, *args, **kwargs):
        res = super()._get_recipient_data(*args, **kwargs)
        if "include_followers" in self.env.context and not self.env.context.get(
            "include_followers"
        ):
            pids = kwargs["pids"]

            def filter_res(x):
                if x[0]:
                    return x[0] in (pids or [])
                if x[1]:
                    return x[1] in (pids or [])

            res = list(filter(filter_res, res))
        return res
