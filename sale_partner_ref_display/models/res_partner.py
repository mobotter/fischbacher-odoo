from odoo import api, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    @api.depends('name', 'ref', 'company_name', 'commercial_company_name')
    def _compute_display_name(self):
        """
        Überschreibt den Anzeigenamen systemweit:
        - ref vorhanden  → "ref - name"
        - ref fehlt      → "id - name"
        """
        for partner in self:
            if partner.name:
                prefix = partner.ref if partner.ref else str(partner.id)
                partner.display_name = f"{prefix} - {partner.name}"
            else:
                # Fallback auf Standard (z.B. bei Kontakten ohne Namen)
                super(ResPartner, partner)._compute_display_name()

    @api.model
    def _name_search(self, name='', domain=None, operator='ilike', limit=100, order=None):
        """
        Sucht gleichzeitig nach ref, name und — wenn numerisch — nach ID.
        """
        domain = domain or []
        if name:
            search_domain = [
                '|', '|',
                ('ref', operator, name),
                ('name', operator, name),
                ('display_name', operator, name),
            ]
            # Numerische Eingabe → auch nach Datenbank-ID suchen
            if name.strip().isdigit():
                search_domain = ['|', ('id', '=', int(name.strip()))] + search_domain

            domain = search_domain + domain

        return super()._name_search(
            name='', domain=domain, operator=operator, limit=limit, order=order
        )
