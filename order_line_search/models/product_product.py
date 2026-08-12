from odoo import models, fields, _

class ProductProduct(models.Model):
    _inherit = 'product.product'

    def action_view_product_sale_order_lines(self):
        """Öffnet die Auftragszeilen, in denen diese Produktvariante vorkommt"""
        self.ensure_one()
        
        return {
            'name': _('Verkaufte Positionen'),
            'type': 'ir.actions.act_window',
            'res_model': 'sale.order.line',
            # Denken Sie an 'list' statt 'tree' für Odoo 19!
            'view_mode': 'list,form,pivot,graph',
            # Filter: Nur Auftragszeilen für exakt dieses Produkt
            'domain': [('product_id', '=', self.id)],
            # Context: Gruppiert die Liste sofort nach Kunde für perfekten Überblick
            'context': {
                'default_product_id': self.id,
                'search_default_group_by_partner': 1,
            }
        }
