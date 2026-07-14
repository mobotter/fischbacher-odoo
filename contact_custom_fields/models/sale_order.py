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

        res = super().write(vals)

        if self.env.context.get('skip_product_pricelist_only'):
            return res

        if 'pricelist_id' in vals:
            for order in self:
                locked_lines = order.order_line.filtered(lambda l: l._should_use_only_product_pricelist())
                normal_lines = order.order_line - locked_lines

                locked_lines._enforce_product_pricelist_only()
                normal_lines._apply_standard_pricelist_price()

        return res

    def action_confirm(self):
        for order in self:
            if order.partner_id.sale_blocked:
                raise UserError(_("Dieser Kunde ist für den Verkauf gesperrt und kann nicht bestätigt werden."))

            locked_lines = order.order_line.filtered(lambda l: l._should_use_only_product_pricelist())
            locked_lines._enforce_product_pricelist_only()

        return super().action_confirm()

    @api.onchange('pricelist_id')
    def _onchange_pricelist_id_reapply_line_prices(self):
        if self.env.context.get('skip_product_pricelist_only'):
            return

        for order in self:
            locked_lines = order.order_line.filtered(lambda l: l._should_use_only_product_pricelist())
            normal_lines = order.order_line - locked_lines

            locked_lines._enforce_product_pricelist_only()
            normal_lines._apply_standard_pricelist_price()


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    def _is_product_pricelist_ready(self):
        self.ensure_one()
        return bool(self.order_id and self.product_id and self.product_uom_id and not self.display_type)

    def _product_uses_only_product_pricelist(self):
        self.ensure_one()
        return bool(self.product_id and self.product_id.product_tmpl_id.use_only_product_pricelist)

    def _should_use_only_product_pricelist(self):
        self.ensure_one()
        return self._is_product_pricelist_ready() and self._product_uses_only_product_pricelist()

    def _get_product_scoped_pricelist_items(self):
        self.ensure_one()
        if not self._should_use_only_product_pricelist():
            return self.env['product.pricelist.item']

        order = self.order_id
        product = self.product_id
        quantity = self.product_uom_qty or 1.0
        date = order.date_order.date() if order and order.date_order else fields.Date.context_today(self)
        company = order.company_id if order else self.env.company

        domain = [
            ('applied_on', 'in', ['0_product_variant', '1_product']),
            '|', ('company_id', '=', False), ('company_id', '=', company.id),
            '|', ('date_start', '=', False), ('date_start', '<=', date),
            '|', ('date_end', '=', False), ('date_end', '>=', date),
            ('min_quantity', '<=', quantity),
        ]

        items = self.env['product.pricelist.item'].search(domain)

        return items.filtered(
            lambda item: (
                (item.applied_on == '0_product_variant' and item.product_id == product)
                or (item.applied_on == '1_product' and item.product_tmpl_id == product.product_tmpl_id)
            )
        )

    def _get_selected_product_pricelist_item(self):
        self.ensure_one()
        items = self._get_product_scoped_pricelist_items()
        if not items:
            return self.env['product.pricelist.item']

        def priority_key(item):
            return (
                0 if item.applied_on == '0_product_variant' else 1,
                -(item.min_quantity or 0.0),
                item.sequence,
                item.id,
            )

        return items.sorted(key=priority_key)[:1]

    def _get_price_from_product_pricelist_rule(self):
        self.ensure_one()

        rule = self._get_selected_product_pricelist_item()
        if not rule:
            return None

        product = self.product_id
        qty = self.product_uom_qty or 1.0

        if rule.compute_price == 'fixed':
            return rule.fixed_price

        if rule.base == 'list_price':
            base_price = product.lst_price
        elif rule.base == 'standard_price':
            base_price = product.standard_price
        elif rule.base == 'pricelist' and rule.base_pricelist_id:
            partner = self.order_id.partner_id if self.order_id else False
            base_price = rule.base_pricelist_id._get_product_price(product, qty, partner)
        else:
            base_price = product.lst_price

        if rule.compute_price == 'percentage':
            return base_price * (1 - (rule.percent_price or 0.0) / 100.0)

        if rule.compute_price == 'formula':
            price = base_price
            if rule.price_discount:
                price = price * (1 - rule.price_discount)
            if rule.price_surcharge:
                price += rule.price_surcharge
            if rule.price_round:
                price = round(price / rule.price_round) * rule.price_round
            if rule.price_min_margin:
                price = max(price, base_price + rule.price_min_margin)
            if rule.price_max_margin:
                price = min(price, base_price + rule.price_max_margin)
            return price

        return base_price

    def _get_standard_pricelist_price(self):
        self.ensure_one()
        if not self.order_id or not self.order_id.pricelist_id or not self.product_id or not self.product_uom_id:
            return None

        line = self.with_context(
            lang=self.order_id.partner_id.lang,
            partner=self.order_id.partner_id.id,
            quantity=self.product_uom_qty,
            date=self.order_id.date_order,
            pricelist=self.order_id.pricelist_id.id,
            uom=self.product_uom_id.id,
            fiscal_position=self.order_id.fiscal_position_id.id if self.order_id.fiscal_position_id else False,
        )
        return line._get_display_price()

    def _apply_standard_pricelist_price(self):
        if self.env.context.get('skip_product_pricelist_only'):
            return

        for line in self:
            if not line._is_product_pricelist_ready():
                continue

            price = line._get_standard_pricelist_price()
            if price is None:
                continue

            rounding = line.currency_id.rounding if line.currency_id else 0.01
            if isclose(line.price_unit, price, rel_tol=0.0, abs_tol=rounding):
                continue

            line.update({
                'price_unit': price,
            })

    def _enforce_product_pricelist_only(self):
        if self.env.context.get('skip_product_pricelist_only'):
            return

        for line in self:
            if not line._should_use_only_product_pricelist():
                continue

            rule = line._get_selected_product_pricelist_item()
            if not rule:
                continue

            target_price = line._get_price_from_product_pricelist_rule()
            if target_price is None:
                continue

            rounding = line.currency_id.rounding if line.currency_id else 0.01
            if isclose(line.price_unit, target_price, rel_tol=0.0, abs_tol=rounding):
                continue

            line.with_context(skip_product_pricelist_only=True).write({
                'price_unit': target_price,
                'discount': 0.0,
            })

    @api.model_create_multi
    def create(self, vals_list):
        lines = super().create(vals_list)
        if self.env.context.get('skip_product_pricelist_only'):
            return lines

        locked = lines.filtered(lambda l: l._should_use_only_product_pricelist())
        normal = lines - locked

        locked._enforce_product_pricelist_only()
        normal._apply_standard_pricelist_price()
        return lines

    def write(self, vals):
        res = super().write(vals)
        if self.env.context.get('skip_product_pricelist_only'):
            return res

        trigger_fields = {'product_id', 'product_uom_id', 'product_uom_qty'}
        if trigger_fields.intersection(vals.keys()):
            locked = self.filtered(lambda l: l._should_use_only_product_pricelist())
            normal = self - locked
            locked._enforce_product_pricelist_only()
            normal._apply_standard_pricelist_price()

        return res

    @api.onchange('product_id', 'product_uom_id', 'product_uom_qty')
    def _onchange_product_pricelist_only(self):
        if self.env.context.get('skip_product_pricelist_only'):
            return

        locked = self.filtered(lambda l: l._should_use_only_product_pricelist())
        normal = self - locked

        locked._enforce_product_pricelist_only()
        normal._apply_standard_pricelist_price()
