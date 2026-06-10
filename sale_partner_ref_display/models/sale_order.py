from odoo import api, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.model
    def fields_get(self, allfields=None, attributes=None):
        """
        Ergänzt den Kontext für das partner_id-Feld,
        damit name_get() den ref-Prefix verwendet.
        """
        result = super().fields_get(allfields=allfields, attributes=attributes)
        if 'partner_id' in result:
            ctx = result['partner_id'].get('context', {})
            if isinstance(ctx, str):
                # Kontext ist manchmal ein String in älteren Definitionen
                ctx = {}
            ctx['show_ref_prefix'] = True
            result['partner_id']['context'] = ctx
        return result
