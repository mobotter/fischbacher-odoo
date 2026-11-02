from odoo import api, fields, models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    partner_recipient_id = fields.Many2one(
        comodel_name="res.partner",
        string="Service Recipient",
        compute="_compute_partner_recipient_id",
        store=True,
        readonly=False,
        check_company=True,
        index="btree_not_null",
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]",
    )

    @api.depends("sale_id", "partner_id")
    def _compute_partner_recipient_id(self):
        for picking in self:
            if picking.sale_id:
                picking.partner_recipient_id = picking.sale_id.partner_recipient_id
            elif picking.partner_id and picking.picking_type_code == "outgoing":
                picking.partner_recipient_id = picking.partner_id._get_recipient_address()
            else:
                picking.partner_recipient_id = picking.partner_recipient_id or False
