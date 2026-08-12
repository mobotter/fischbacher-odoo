from odoo import models, fields

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    # DIESES Feld hat in Odoo vorher gefehlt!
    product_cost = fields.Float(
        related='product_id.standard_price', 
        string='Einkaufspreis (Produkt)', 
        readonly=True
    )

    def action_open_product(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'product.product',
            'res_id': self.product_id.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_open_partner(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'res.partner',
            'res_id': self.order_partner_id.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_open_order(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'sale.order',
            'res_id': self.order_id.id,
            'view_mode': 'form',
            'target': 'current',
        }
