from odoo import fields, models, api
from datetime import timedelta

class AccountMove(models.Model):
    _inherit = 'account.move'

    extended_date = fields.Date(
        string="Extended Date",
        compute="_compute_discounted_amount",
        store=True
    )
    discount_amount = fields.Float(
        string="Discounted Amount",
        compute="_compute_discounted_amount",
        store=True
    )

    @api.depends(
        'invoice_date',
        'amount_total',
        'invoice_payment_term_id',
        'invoice_payment_term_id.early_discount',
        'invoice_payment_term_id.discount_days',
        'invoice_payment_term_id.discount_percentage'
    )
    def _compute_discounted_amount(self):
        for rec in self:
            rec.extended_date = False
            rec.discount_amount = 0.0

            if rec.invoice_payment_term_id and rec.invoice_payment_term_id.early_discount and rec.invoice_payment_term_id.discount_days and rec.invoice_payment_term_id.discount_percentage:
                if rec.invoice_date:
                    rec.extended_date = rec.invoice_date + timedelta(
                        days=rec.invoice_payment_term_id.discount_days
                    )
                rec.discount_amount = rec.amount_total - (rec.amount_total * rec.invoice_payment_term_id.discount_percentage)


