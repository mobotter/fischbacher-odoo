from odoo import api, fields, models
from dateutil.relativedelta import relativedelta

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    billing_period_start = fields.Date(compute='_compute_billing_period', store=True)
    billing_period_end = fields.Date(compute='_compute_billing_period', store=True)

    @api.depends('start_date', 'next_invoice_date')
    def _compute_billing_period(self):
        for order in self:
            if order.next_invoice_date:
                order.billing_period_end = order.next_invoice_date - relativedelta(days=1)
                order.billing_period_start = order.next_invoice_date - relativedelta(days=28)
            else:
                order.billing_period_start = order.start_date
                order.billing_period_end = order.start_date
