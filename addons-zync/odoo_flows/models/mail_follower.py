from odoo import _, api, fields, models, SUPERUSER_ID
from odoo.exceptions import UserError, RedirectWarning, ValidationError


class MailFollower(models.Model):
    _inherit = "mail.followers"

    def _get_recipient_data(self, records, *args, **kwargs):
        if 'of_notify_partner_ids' in self.env.context:
            if "include_followers" in self.env.context and not self.env.context.get(
                "include_followers"
            ):
                # so exclude followers
                default_partners = records.mapped('message_follower_ids.partner_id')
                pids = kwargs["pids"] or []
                pids += list(set(self.env.context['of_notify_partner_ids']))
                for x in default_partners:
                    if x.id in pids:
                        pids.remove(x.id)
                kwargs['pids'] = pids
                record_ids = records.ids
                records = records.browse()
                res2 = super()._get_recipient_data(records, *args, **kwargs)
                res = {x: res2[0] for x in record_ids}

        else:
            res = super()._get_recipient_data(records, *args, **kwargs)
        return res
