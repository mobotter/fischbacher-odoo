from odoo import models, fields, _

class ResPartner(models.Model):
    _inherit = 'res.partner'

    def action_view_sale_order_lines(self):
        """Öffnet die Auftragszeilen für diesen speziellen Kunden"""
        self.ensure_one()
        
        # Action-Definition zurückgeben
        return {
            'name': _('Auftragszeilen'),
            'type': 'ir.actions.act_window',
            'res_model': 'sale.order.line',
            # Kanäle/Ansichten die wir öffnen wollen
            'view_mode': 'list,form,pivot,graph',
            # Nur die Positionen dieses Kunden anzeigen.
            # Durch child_of erwischen wir auch Lieferadressen und Ansprechpartner dieses Kunden!
            'domain': [('order_partner_id', 'child_of', self.id)],
            # context sorgt dafür, dass bei Neuanlage (falls doch erlaubt) der Kunde gesetzt ist, 
            # und gruppiert die Baumansicht evtl. direkt nach Produkt.
            'context': {
                'default_order_partner_id': self.id,
                'search_default_group_by_product': 1,
            }
        }
