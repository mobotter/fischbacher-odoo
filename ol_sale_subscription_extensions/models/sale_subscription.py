from dateutil.relativedelta import relativedelta

from odoo import api, fields, models


class SaleSubscription(models.Model):
    _inherit = 'sale.subscription'

    billing_timing = fields.Selection(
        related='recurring_plan_id.billing_timing',
        string='Abrechnungszeitpunkt',
        store=True,
        readonly=True,
    )

    def _get_initial_next_invoice_date_from_plan(self):
        self.ensure_one()
        if not self.date_start or not self.recurring_plan_id:
            return False

        timing = self.recurring_plan_id.billing_timing
        start_date = fields.Date.to_date(self.date_start)
        period_value = self.recurring_plan_id.billing_period_value or 0
        period_unit = self.recurring_plan_id.billing_period_unit

        if timing == 'advance':
            return start_date

        if timing == 'arrears':
            delta_map = {
                'day': {'days': period_value},
                'week': {'weeks': period_value},
                'month': {'months': period_value},
                'year': {'years': period_value},
            }
            delta_kwargs = delta_map.get(period_unit)
            if delta_kwargs:
                return start_date + relativedelta(**delta_kwargs)
        return start_date

    def _can_auto_reset_initial_invoice_date(self):
        self.ensure_one()
        moves = self.env['account.move'].search_count([
            ('subscription_id', '=', self.id),
            ('move_type', '=', 'out_invoice'),
            ('state', '!=', 'cancel'),
        ])
        return not moves

    def _apply_billing_timing_next_invoice_date(self, force=False):
        for subscription in self:
            if not subscription.date_start or not subscription.recurring_plan_id:
                continue
            if not force and not subscription._can_auto_reset_initial_invoice_date():
                continue

            next_date = subscription._get_initial_next_invoice_date_from_plan()
            if next_date:
                subscription.next_invoice_date = next_date

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        records._apply_billing_timing_next_invoice_date()
        return records

    def write(self, vals):
        tracked_fields = {'recurring_plan_id', 'date_start'}
        should_recompute = bool(tracked_fields.intersection(vals.keys()))
        res = super().write(vals)
        if should_recompute:
            self._apply_billing_timing_next_invoice_date()
        return res
