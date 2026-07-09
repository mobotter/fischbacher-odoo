from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    partner_id = fields.Many2one(
        'res.partner',
        string='Customer',
        required=True,
        change_default=True,
        index=True,
        tracking=1,
        domain="""
            [
                ('type', '!=', 'private'),
                ('sale_blocked', '=', False)
            ]
        """,
    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            partner_id = vals.get('partner_id')
            if partner_id:
                partner = self.env['res.partner'].browse(partner_id)
                if partner.sale_blocked:
                    raise ValidationError(
                        _("Dieser Kunde ist für den Verkauf gesperrt.")
                    )
        return super().create(vals_list)

    def write(self, vals):
        if vals.get('partner_id'):
            partner = self.env['res.partner'].browse(vals['partner_id'])
            if partner.sale_blocked:
                raise ValidationError(
                    _("Dieser Kunde ist für den Verkauf gesperrt.")
                )
        return super().write(vals)

    def action_confirm(self):
        for order in self:
            if order.partner_id.sale_blocked:
                raise ValidationError(
                    _("Dieser Kunde ist für den Verkauf gesperrt und kann nicht bestätigt werden.")
                )
        return super().action_confirm()
