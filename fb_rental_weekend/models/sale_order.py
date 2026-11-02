from datetime import datetime, time, timedelta
from math import ceil
import pytz
from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    fb_charge_weekends = fields.Boolean(
        string="Wochenende berechnen", default=False, copy=True,
        help="Aktiv: native Mietpreise inklusive Wochenende. Inaktiv: Samstag und "
             "Sonntag sind mietpreisfrei. Reservierungsdaten bleiben unverändert.",
    )

    @staticmethod
    def _fb_weekday_seconds(start, end, tz):
        start = pytz.UTC.localize(start)
        end = pytz.UTC.localize(end)
        day = start.astimezone(tz).date()
        last = end.astimezone(tz).date()
        seconds = 0.0
        while day <= last:
            if day.weekday() < 5:
                lo = max(start, tz.localize(datetime.combine(day, time.min)).astimezone(pytz.UTC))
                hi = min(end, tz.localize(datetime.combine(day + timedelta(days=1), time.min)).astimezone(pytz.UTC))
                if hi > lo:
                    seconds += (hi - lo).total_seconds()
            day += timedelta(days=1)
        return seconds

    def _fb_get_billable_seconds(self):
        self.ensure_one()
        start = fields.Datetime.to_datetime(self.rental_start_date)
        end = fields.Datetime.to_datetime(self.rental_return_date)
        if not start or not end or end <= start:
            return 0.0
        if self.fb_charge_weekends:
            return (end - start).total_seconds()
        tz = pytz.timezone(self.company_id.partner_id.tz or "Europe/Berlin")
        return self._fb_weekday_seconds(start, end, tz)

    @api.depends("rental_start_date", "rental_return_date", "fb_charge_weekends",
                 "is_rental_order", "company_id", "company_id.partner_id.tz")
    def _compute_duration(self):
        super()._compute_duration()
        for order in self:
            if not order.fb_charge_weekends and order.is_rental_order:
                days, seconds = divmod(order._fb_get_billable_seconds(), 86400)
                order.duration_days = int(days)
                order.remaining_hours = ceil(seconds / 3600)

    def _fb_refresh_rental_prices(self):
        if self.env.context.get("fb_weekend_refresh"):
            return
        for order in self:
            if order.state in ("draft", "sent") and order.order_line.filtered("is_rental"):
                order.with_context(fb_weekend_refresh=True)._recompute_rental_prices()
                order.show_update_duration = False

    @api.onchange("fb_charge_weekends", "rental_start_date", "rental_return_date")
    def _fb_onchange_weekend_prices(self):
        self._fb_refresh_rental_prices()

    def write(self, vals):
        result = super().write(vals)
        if {"fb_charge_weekends", "rental_start_date", "rental_return_date"}.intersection(vals):
            self._fb_refresh_rental_prices()
        return result
