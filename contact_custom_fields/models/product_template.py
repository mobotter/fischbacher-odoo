from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    strict_pricelist_lock = fields.Boolean(
        string='rabattfähig',
        default=True,
        help='Wenn deaktiviert, sind manuelle Rabatte auf der Auftragszeile verboten. Es sind nur produktbezogene Festpreis-Regeln aus Preislisten zulässig.'
    )
