from odoo import api, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    @api.depends_context('show_ref_prefix')
    @api.depends('name', 'ref', 'company_name', 'commercial_company_name')
    def _compute_display_name(self):
        if not self.env.context.get('show_ref_prefix'):
            return super()._compute_display_name()

        for partner in self:
            if partner.name:
                prefix = partner.ref or str(partner.id)
                partner.display_name = f"{prefix} - {partner.name}"
            else:
                super(ResPartner, partner)._compute_display_name()

    @api.model
    def _name_search(self, name='', domain=None, operator='ilike', limit=100, order=None):
        """
        Erweitert die Suche um ref, name, commercial_company_name, company_name, short_term, email, phone, mobile.
        Sucht in ALLEN Kontakten (unabhngig von customer_rank oder supplier_rank).
        """
        domain = list(domain or [])
        if name and self.env.context.get('show_ref_prefix'):
            search_domain = [
                '|', '|', '|', '|', '|', '|', '|',
                ('ref', operator, name),
                ('name', operator, name),
                ('commercial_company_name', operator, name),
                ('company_name', operator, name),
                ('short_term', operator, name),
                ('email', operator, name),
                ('phone', operator, name),
                ('mobile', operator, name),
            ]
            # Suche nach ID, wenn name eine Zahl ist
            if name.strip().isdigit():
                search_domain = ['|', ('id', '=', int(name.strip()))] + search_domain
            domain = search_domain + domain
            name = ''
        return super()._name_search(name=name, domain=domain, operator=operator, limit=limit, order=order)
