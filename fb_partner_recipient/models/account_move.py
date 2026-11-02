from odoo import api, fields, models


class AccountMove(models.Model):
    _inherit = "account.move"

    partner_recipient_id = fields.Many2one(
        comodel_name="res.partner",
        string="Service Recipient",
        compute="_compute_partner_recipient_id",
        store=True,
        readonly=False,
        precompute=True,
        tracking=True,
        check_company=True,
        index="btree_not_null",
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]",
    )

    @api.depends("partner_id")
    def _compute_partner_recipient_id(self):
        for move in self:
            if move.partner_id and move.is_sale_document(include_receipts=True):
                move.partner_recipient_id = move.partner_id._get_recipient_address()
            else:
                move.partner_recipient_id = False
