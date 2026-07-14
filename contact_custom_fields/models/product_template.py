from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    strict_pricelist_lock = fields.Boolean(
        string='Strenge Preislisten-Sperre',
        help='Wenn aktiviert, sind manuelle Rabatte verboten. Es sind nur produktbezogene Festpreis-Regeln aus Preislisten zulässig.'
    )
