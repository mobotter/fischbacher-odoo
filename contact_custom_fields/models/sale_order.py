from math import isclose

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    partner_id = fields.Many2one(
        'res.partner',
        string='Customer',
        required=True,
        change_default=True,
        index=True,
        tracking=1,
        domain="[('sale_blocked', '=', False), ('customer_rank', '>', 0), ('parent_id', '=', False)]",
    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            partner_id = vals.get('partner_id')
            if partner_id:
                partner = self.env['res.partner'].browse(partner_id)
                if partner.sale_blocked:
                    raise UserError(_("Dieser Kunde ist für den Verkauf gesperrt."))
        return super().create(vals_list)

    def write(self, vals):
        if vals.get('partner_id'):
            partner = self.env['res.partner'].browse(vals['partner_id'])
            if partner.sale_blocked:
                raise UserError(_("Dieser Kunde ist für den Verkauf gesperrt."))
        return super().write(vals)

    def action_confirm(self):
        for order in self:
            if order.partner_id.sale_blocked:
                raise UserError(_("Dieser Kunde ist für den Verkauf gesperrt und kann nicht bestätigt werden."))

            locked_lines = order.order_line.filtered(lambda l: l._should_apply_strict_lock())
            locked_lines._enforce_strict_locked_price()

        return super().action_confirm()


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    def _is_strict_lock_ready(self):
        self.ensure_one()
        return bool(
            self.order_id
            and self.order_id.pricelist_id
            and self.product_id
            and self.product_uom_id
            and not self.display_type
        )

    def _product_has_strict_lock(self):
        self.ensure_one()
        return bool(self.product_id and not self.product_id.product_tmpl_id.strict_pricelist_lock)

    def _should_apply_strict_lock(self):
        self.ensure_one()
        return self._is_strict_lock_ready() and self._product_has_strict_lock()

    def _get_allowed_fixed_pricelist_items(self):
        self.ensure_one()
        if not self._should_apply_strict_lock():
            return self.env['product.pricelist.item']

        order = self.order_id
        pricelist = order.pricelist_id
        product = self.product_id
        quantity = self.product_uom_qty or 1.0
        date = order.date_order.date() if order.date_order else fields.Date.context_today(self)
        company = order.company_id

        domain = [
            ('pricelist_id', '=', pricelist.id),
            ('compute_price', '=', 'fixed'),
            ('applied_on', 'in', ['0_product_variant', '1_product']),
            '|', ('company_id', '=', False), ('company_id', '=', company.id),
            '|', ('date_start', '=', False), ('date_start', '<=', date),
            '|', ('date_end', '=', False), ('date_end', '>=', date),
            ('min_quantity', '<=', quantity),
        ]

        items = self.env['product.pricelist.item'].search(domain)

        items = items.filtered(
            lambda item: (
                (item.applied_on == '0_product_variant' and item.product_id == product)
                or (item.applied_on == '1_product' and item.product_tmpl_id == product.product_tmpl_id)
            )
        )
        return items

    def _get_strict_fixed_price_rule(self):
        self.ensure_one()
        items = self._get_allowed_fixed_pricelist_items()
        if not items:
            return self.env['product.pricelist.item']

        def priority_key(item):
            applied_on_rank = {
                '0_product_variant': 0,
                '1_product': 1,
            }
            return (
                applied_on_rank.get(item.applied_on, 99),
                -(item.min_quantity or 0.0),
                item.id,
            )

        return items.sorted(key=priority_key)[:1]

    def _get_strict_locked_price(self):
        self.ensure_one()
        rule = self._get_strict_fixed_price_rule()
        return rule.fixed_price if rule else None

    def _enforce_strict_locked_price(self):
        if self.env.context.get('skip_strict_pricelist_lock'):
            return

        for line in self:
            if not line._should_apply_strict_lock():
                continue

            locked_price = line._get_strict_locked_price()
            if locked_price is None:
                raise UserError(_(
                    "Für '%s' fehlt in der aktiven Preisliste ein artikelbezogener Festpreis."
                ) % line.product_id.display_name)

            rounding = line.currency_id.rounding if line.currency_id else 0.01
            if isclose(line.price_unit, locked_price, rel_tol=0.0, abs_tol=rounding):
                continue

            line.with_context(skip_strict_pricelist_lock=True).write({
                'price_unit': locked_price,
            })

    @api.model_create_multi
    def create(self, vals_list):
        lines = super().create(vals_list)
        if not self.env.context.get('skip_strict_pricelist_lock'):
            lines.filtered(lambda l: l._should_apply_strict_lock())._enforce_strict_locked_price()
        return lines

    def write(self, vals):
        res = super().write(vals)
        if self.env.context.get('skip_strict_pricelist_lock'):
            return res

        trigger_fields = {'product_id', 'product_uom_id', 'product_uom_qty', 'order_id', 'price_unit'}
        if trigger_fields.intersection(vals.keys()) and 'discount' not in vals:
            self.filtered(lambda l: l._should_apply_strict_lock())._enforce_strict_locked_price()

        return res

    @api.onchange('product_id', 'product_uom_id', 'product_uom_qty', 'order_id.pricelist_id')
    def _onchange_strict_pricelist_lock(self):
        if self.env.context.get('skip_strict_pricelist_lock'):
            return

        self.filtered(lambda l: l._should_apply_strict_lock())._enforce_strict_locked_price()
