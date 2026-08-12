from odoo import models, fields, _

class ResPartner(models.Model):
    _inherit = 'res.partner'

    def action_view_sale_order_lines(self):
        self.ensure_one()
        
        # ID unserer eigens erstellten Listenansicht holen
        list_view_id = self.env.ref('order_line_search.view_order_line_tree_custom').id
        
        return {
            'name': _('Auftragszeilen'),
            'type': 'ir.actions.act_window',
            'res_model': 'sale.order.line',
            'view_mode': 'list,form,pivot,graph',
            # Hier weisen wir Odoo an, genau diese Listenansicht zu nutzen:
            'views': [(list_view_id, 'list'), (False, 'form'), (False, 'pivot'), (False, 'graph')],
            'domain': [('order_partner_id', 'child_of', self.id)],
            'context': {
                'default_order_partner_id': self.id,
            }
        }
