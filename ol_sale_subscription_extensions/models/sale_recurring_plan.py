from odoo import fields, models


class SaleSubscriptionPlan(models.Model):
    _inherit = 'sale.subscription.plan'

    billing_timing = fields.Selection(
        selection=[
            ('advance', 'Im Voraus'),
            ('arrears', 'Im Nachhinein'),
        ],
        string='Abrechnungszeitpunkt',
        required=True,
        default='advance',
        help='Steuert, ob die erste wiederkehrende Rechnung zum Periodenbeginn oder nach Ablauf der ersten Periode erzeugt wird.',
    )
