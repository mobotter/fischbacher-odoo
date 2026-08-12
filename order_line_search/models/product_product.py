from odoo import models, fields, _

# 1. Funktion für die Variante
class ProductProduct(models.Model):
    _inherit = 'product.product'

    def action_view_product_sale_order_lines(self):
        self.ensure_one()
        return {
            'name': _('Verkaufte Positionen'),
            'type': 'ir.actions.act_window',
            'res_model': 'sale.order.line',
            'view_mode': 'list,form,pivot,graph',
            'domain': [('product_id', '=', self.id)],
            'context': {
                'default_product_id': self.id,
                'search_default_group_by_partner': 1,
            }
        }

# 2. Funktion für die Produktvorlage (Template)
class ProductTemplate(models.Model):
    _inherit = 'product.template'

    def action_view_product_sale_order_lines(self):
        self.ensure_one()
        # Bei der Vorlage holen wir alle Varianten-IDs
        variant_ids = self.product_variant_ids.ids
        return {
            'name': _('Verkaufte Positionen (Alle Varianten)'),
            'type': 'ir.actions.act_window',
            'res_model': 'sale.order.line',
            'view_mode': 'list,form,pivot,graph',
            'domain': [('product_id', 'in', variant_ids)],
            'context': {
                'search_default_group_by_partner': 1,
            }
        }
