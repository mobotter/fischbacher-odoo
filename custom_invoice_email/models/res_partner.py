from odoo import models, fields, api
from odoo.exceptions import UserError
from markupsafe import Markup
from odoo import fields, models, _
from odoo import models
from odoo.tools import email_normalize 
from markupsafe import Markup

class ResPartner(models.Model):
    _inherit = 'res.partner'


    # Task Id 50960
    # Computed field: auto-fetch invoice address email
    invoice_address_email = fields.Char(
        string="Invoice Email",
        store=True
    )

    # Editable field: initially set to invoice_address_email
    invoice_email_manual = fields.Char(
        string="Invoice Email"
    )
    # Task id 50960


    # task Id 50975
    advertising_exclusion = fields.Boolean(
            string="Advertising Exclusion",
            default=False,
            help="If checked, this contact will be added to the email blacklist "
                 "and will not receive marketing/advertising emails."
        )
    # task Id 50975

    # advertising_email = fields.Char(
    #     string="Advertising E-Mail",
    #     store = True
    # )

    # Task id 50960
    def _compute_invoice_address_email(self):
        for partner in self:
            # Look for child contact of type 'invoice'
            invoice_address = partner.child_ids.filtered(lambda c: c.type == 'invoice')
            if invoice_address and (not invoice_address[-1].email or invoice_address[-1].email != partner.invoice_address_email):
                # raise UserError("working")
                partner.invoice_address_email = invoice_address[-1].email or ''


    # Task Id 51018 JC
    advertising_email = fields.Char(
        string="Advertising E-Mail",
        store = True,
        tracking=True,
    )

    @api.model
    def create(self, vals):
        partner = super(ResPartner, self).create(vals)
        if not partner.advertising_email and partner.email:
            partner.advertising_email = partner.email
        return partner
    # Task Id 51018 JC






    #         if 'invoice_address_email' in vals:
    #             invoice_address = partner.child_ids.filtered(lambda c: c.type == 'invoice')
    #             if invoice_address and (not invoice_address[-1].email or invoice_address[-1].email != partner.invoice_address_email):
    #                 invoice_address[-1].email = partner.invoice_address_email  or '' 
                    
    #         if 'advertising_exclusion' in vals:
    #             old_values = {p.id: p.advertising_exclusion for p in self}
    #             raise UserError(str(old_values))
    #             res = super().write(vals)
    #             blacklist_model = self.env['mail.blacklist']
    #             new_val = vals['advertising_exclusion']
    #             old_val = old_values[partner.id]
    #             if new_val == old_val:
    #                 continue
    
    #             email_norm = partner.email_normalized
    #             if not email_norm:
    #                 continue
    
    #             if new_val:
    #                 if not blacklist_model._search([('email', '=', email_norm)]):
    #                     blacklist_model.sudo().create({
    #                         'email': email_norm,
    #                         'active': True,
    #                     })
    #                 partner._compute_is_blacklisted()
    
    #             else: 
    #                 bl_record = blacklist_model._search([('email', '=', email_norm)])
    #                 if bl_record:
    #                     bl_record.unlink()
    #                 partner._compute_is_blacklisted()
                    

    #     return res

    def write(self, vals):
        old_advertising_values = {}
        if 'advertising_exclusion' in vals:
            old_advertising_values = {p.id: p.advertising_exclusion for p in self}
    
        res = super(ResPartner, self).write(vals)
    
        for partner in self:
            if 'child_ids' in vals:
                partner._compute_invoice_address_email()
    
            if 'invoice_address_email' in vals:
                invoice_address = partner.child_ids.filtered(lambda c: c.type == 'invoice')
                if invoice_address:
                    new_email = partner.invoice_address_email or False
                    if invoice_address[-1].email != new_email:
                        invoice_address[-1].write({'email': new_email})
                        
                if partner.invoice_address_email and not invoice_address:  # Only create if we have an email to set
                    invoice_address = partner.child_ids.create({
                        'parent_id': partner.id,
                        'type': 'invoice',
                        'name': partner.name,
                        'email': partner.invoice_address_email,
                        'street': partner.street,
                        'street2': partner.street2,
                        'city': partner.city,
                        'zip': partner.zip,
                        'country_id': partner.country_id.id,
                        'state_id': partner.state_id.id,
                        'is_company': False,
                    })
    
            if 'advertising_exclusion' in vals:
                new_val = vals['advertising_exclusion']
                old_val = old_advertising_values.get(partner.id, not new_val)  # fallback safe
    
                if new_val == old_val:
                    continue
    
                email_norm = partner.advertising_email
                if not email_norm:
                    continue
    
                blacklist_model = self.env['mail.blacklist'].sudo()
    
                if not blacklist_model.search([('email', '=', email_norm)], limit=1):
                    blacklist_model.create({
                        'email': email_norm,
                        'active': True,
                    })
                else:  
                    bl_record = blacklist_model.search([('email', '=', email_norm)], limit=1)
                    if bl_record:
                        bl_record.unlink()
                partner._compute_is_blacklisted()
                
        #     if 'email' in vals:
        #         if partner.email and (partner.email != partner.advertising_email):
        #             partner.write({'advertising_email': partner.email})
                    
            # if 'advertising_email' in vals:
        #         if partner.advertising_email and (partner.email != partner.advertising_email):
        #             partner.write({'email': partner.advertising_email})
            # Task Id 51018 JC
            if 'email' in vals and not partner.advertising_email:
                partner.advertising_email = vals['email']
            # Task Id 51018 JC
        return res

# task Id 50975
class MailBlacklistRemove(models.TransientModel):
    _inherit = 'mail.blacklist.remove'

    def action_unblacklist_apply(self):
        """
        Override the default unblacklist action.
        When an email is removed from the blacklist,
        we also set advertising_exclusion = False on the related partner(s).
        """
        result = super(MailBlacklistRemove, self).action_unblacklist_apply()

        email_normalized = email_normalize(self.email)

        if not email_normalized:
            return result

        partners = self.env['res.partner'].search([
            ('email_normalized', '=', email_normalized)
        ])

        if partners:
            partners.sudo().write({'advertising_exclusion': False})
            reason = self.reason or _("Removed from blacklist via wizard")
            message = Markup("<p><em>%s</em></p><p>%s</p>") % (
                _("Automatically unmarked from advertising exclusion"),
                _("Reason: %s") % reason
            )
            for partner in partners:
                partner.message_post(body=message, subject=_("Blacklist Removal"))

        return result
# task Id 50975