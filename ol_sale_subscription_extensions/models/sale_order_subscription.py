from dateutil.relativedelta import relativedelta

from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def _get_initial_next_invoice_date_from_plan(self):
        self.ensure_one()
        if not self.is_subscription or not self.plan_id or not self.start_date:
            return False

        timing = getattr(self.plan_id, 'billing_timing', 'advance')
        start_date = fields.Date.to_date(self.start_date)

        if timing == 'advance':
            return start_date

        period_value = self.plan_id.billing_period_value or 0
        period_unit = self.plan_id.billing_period_unit

        delta_map = {
            'day': {'days': period_value},
            'week': {'weeks': period_value},
            'month': {'months': period_value},
            'year': {'years': period_value},
        }
        delta_kwargs = delta_map.get(period_unit)
        return start_date + relativedelta(**delta_kwargs) if delta_kwargs else start_date

    def _can_auto_reset_initial_invoice_date(self):
        self.ensure_one()
        return not self.invoice_ids

    def _apply_subscription_billing_timing(self, force=False):
        for order in self:
            if not order.is_subscription or not order.plan_id or not order.start_date:
                continue
            if not force and not order._can_auto_reset_initial_invoice_date():
                continue

            next_date = order._get_initial_next_invoice_date_from_plan()
            if next_date:
                order.next_invoice_date = next_date

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        records._apply_subscription_billing_timing()
        return records

    def write(self, vals):
        watched = {'plan_id', 'start_date'}
        res = super().write(vals)
        if watched.intersection(vals.keys()):
            self._apply_subscription_billing_timing()
        return res
