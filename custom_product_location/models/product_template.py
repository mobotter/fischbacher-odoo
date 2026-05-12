from odoo import models, fields, api

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    location_names = fields.Char(
        string='Lagerorte',
        compute='_compute_location_names',
        store=False,
    )

    def _compute_location_names(self):
        for tmpl in self:
            quants = self.env['stock.quant'].search([
                ('product_id.product_tmpl_id', '=', tmpl.id),
                ('location_id.usage', '=', 'internal'),
                ('quantity', '>', 0),
            ])
            locations = quants.mapped('location_id.complete_name')
            tmpl.location_names = ', '.join(locations) if locations else '—'
