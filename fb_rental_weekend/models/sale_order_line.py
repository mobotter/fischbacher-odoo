from datetime import timedelta
from odoo import api, fields, models


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    @api.depends("order_id.fb_charge_weekends", "order_id.rental_start_date",
                 "order_id.rental_return_date", "order_id.company_id.partner_id.tz")
    def _compute_price_unit(self):
        super()._compute_price_unit()

    def _get_pricelist_price(self):
        self.ensure_one()
        order = self.order_id
        if not self.is_rental or order.fb_charge_weekends:
            return super()._get_pricelist_price()
        order._rental_set_dates()
        seconds = order._fb_get_billable_seconds()
        if seconds <= 0:
            return 0.0
        return order.pricelist_id._get_product_price(
            self.product_id.with_context(**self._get_product_price_context()),
            self.product_uom_qty or 1.0,
            currency=self.currency_id,
            uom=self.product_uom_id,
            date=order.date_order or fields.Date.today(),
            start_date=self.start_date,
            end_date=self.start_date + timedelta(seconds=seconds),
        )
