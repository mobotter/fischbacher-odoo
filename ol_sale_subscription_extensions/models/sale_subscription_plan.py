from odoo import fields, models


class SaleSubscriptionPlan(models.Model):
    _inherit = 'sale.subscription.plan'

    billing_timing = fields.Selection(
        selection=[
            ('advance', 'In advance'),
            ('arrears', 'In arrears'),
        ],
        string='Billing Timing',
        required=True,
        default='advance',
        help='Controls whether the first recurring invoice is generated at the beginning of the period or after the first period ends.',
    )
