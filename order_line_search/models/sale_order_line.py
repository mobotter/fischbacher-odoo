from odoo import models, fields

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    # Einkaufspreis vom Produkt holen
    product_cost = fields.Float(
        related='product_id.standard_price', 
        string='Einkaufspreis (Produkt)', 
        readonly=True
    )
    
    # WIR LEGEN DAS FELD SELBST AN!
    # Wenn Odoo das Modul 'sale_stock' installiert hat, wird Odoo diese Definition 
    # einfach mit der eigenen verschmelzen. Wenn nicht, haben wir das Feld erschaffen 
    # und können es in der XML-Ansicht nutzen, ohne dass Odoo abstürzt!
    route_id = fields.Many2one(
        'stock.route',
        string='Route',
        domain=[('sale_selectable', '=', True)],
        ondelete='restrict',
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
