from odoo import api, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    def _get_ref_display_name(self):
        """
        Gibt 'ref - name' zurück, wenn ref gesetzt ist.
        Andernfalls 'id - name'.
        """
        self.ensure_one()
        prefix = self.ref if self.ref else str(self.id)
        return f"{prefix} - {self.name}"

    @api.model
    def _name_search(self, name='', domain=None, operator='ilike', limit=100, order=None):
        """
        Überschreibt die Suche, damit beim Tippen auch nach ref gesucht wird.
        """
        domain = domain or []
        if name:
            search_domain = [
                '|', '|',
                ('ref', operator, name),
                ('name', operator, name),
                ('display_name', operator, name),
            ]
            domain = search_domain + domain

        return super()._name_search(
            name='', domain=domain, operator=operator, limit=limit, order=order
        )

    def name_get(self):
        """
        Gibt für alle Partner in sale-Kontext 'ref - name' zurück.
        Der Kontext 'show_ref_prefix' wird vom sale.order-Modell gesetzt.
        """
        context = self.env.context
        if context.get('show_ref_prefix'):
            result = []
            for partner in self:
                prefix = partner.ref if partner.ref else str(partner.id)
                result.append((partner.id, f"{prefix} - {partner.name}"))
            return result
        return super().name_get()
