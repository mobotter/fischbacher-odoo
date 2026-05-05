from markupsafe import Markup

from odoo import api, fields, models, _
from odoo.tools import email_normalize


class ResPartner(models.Model):
    _inherit = 'res.partner'

    invoice_address_email = fields.Char(
        string="Invoice Email Address",
        store=True
    )

    invoice_email_manual = fields.Char(
        string="Invoice Email"
    )

    advertising_exclusion = fields.Boolean(
        string="Advertising Exclusion",
        default=False,
        help="If checked, this contact will be added to the email blacklist "
             "and will not receive marketing/advertising emails.",
    )

    advertising_email = fields.Char(
        string="Advertising E-Mail",
        store=True,
    )

    @api.depends('child_ids', 'child_ids.type', 'child_ids.email')
    def _compute_invoice_address_email(self):
        for partner in self:
            invoice_address = partner.child_ids.filtered(lambda c: c.type == 'invoice')
            partner.invoice_address_email = invoice_address[-1].email if invoice_address else False

    def _inverse_invoice_address_email(self):
        for partner in self:
            invoice_address = partner.child_ids.filtered(lambda c: c.type == 'invoice')[-1:]
            new_email = partner.invoice_address_email or False

            if invoice_address:
                if invoice_address.email != new_email:
                    invoice_address.write({'email': new_email})
            elif new_email:
                self.env['res.partner'].create({
                    'parent_id': partner.id,
                    'type': 'invoice',
                    'name': partner.name,
                    'email': new_email,
                    'street': partner.street,
                    'street2': partner.street2,
                    'city': partner.city,
                    'zip': partner.zip,
                    'country_id': partner.country_id.id,
                    'state_id': partner.state_id.id,
                    'is_company': False,
                })

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('advertising_email') and vals.get('email'):
                vals['advertising_email'] = vals['email']

        partners = super().create(vals_list)
        partners._sync_advertising_blacklist_on_create()
        return partners

    def write(self, vals):
        old_exclusion = {}
        if 'advertising_exclusion' in vals:
            old_exclusion = {partner.id: partner.advertising_exclusion for partner in self}

        res = super().write(vals)

        if 'email' in vals:
            for partner in self.filtered(lambda p: not p.advertising_email and p.email):
                partner.advertising_email = partner.email

        if 'advertising_exclusion' in vals or 'advertising_email' in vals:
            self._sync_advertising_blacklist(old_exclusion=old_exclusion)

        return res

    def _sync_advertising_blacklist_on_create(self):
        self._sync_advertising_blacklist()

    def _sync_advertising_blacklist(self, old_exclusion=None):
        blacklist_model = self.env['mail.blacklist'].sudo()
        old_exclusion = old_exclusion or {}

        for partner in self:
            new_val = partner.advertising_exclusion
            old_val = old_exclusion.get(partner.id)

            if old_val is not None and new_val == old_val:
                continue

            email_norm = email_normalize(partner.advertising_email or partner.email)
            if not email_norm:
                continue

            blacklist_record = blacklist_model.search([('email', '=', email_norm)], limit=1)

            if new_val:
                if not blacklist_record:
                    blacklist_model.create({
                        'email': email_norm,
                        'active': True,
                    })
            else:
                if blacklist_record:
                    blacklist_record.unlink()

            partner._compute_is_blacklisted()


class MailBlacklistRemove(models.TransientModel):
    _inherit = 'mail.blacklist.remove'

    def action_unblacklist_apply(self):
        result = super().action_unblacklist_apply()

        email_normalized = email_normalize(self.email)
        if not email_normalized:
            return result

        partners = self.env['res.partner'].search([
            '|',
            ('email_normalized', '=', email_normalized),
            ('advertising_email', '=', email_normalized),
        ])

        if partners:
            partners.sudo().write({'advertising_exclusion': False})
            reason = self.reason or _("Removed from blacklist via wizard")
            message = Markup("<p><em>%s</em></p><p>%s</p>") % (
                _("Automatically unmarked from advertising exclusion"),
                _("Reason: %s") % reason,
            )
            for partner in partners:
                partner.message_post(
                    body=message,
                    subject=_("Blacklist Removal"),
                )

        return result
# task Id 50975