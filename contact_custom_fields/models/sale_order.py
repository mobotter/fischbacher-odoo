from math import isclose

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


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
                    raise ValidationError(_("Dieser Kunde ist für den Verkauf gesperrt."))
        return super().create(vals_list)

    def write(self, vals):
        if vals.get('partner_id'):
            partner = self.env['res.partner'].browse(vals['partner_id'])
            if partner.sale_blocked:
                raise ValidationError(_("Dieser Kunde ist für den Verkauf gesperrt."))
        return super().write(vals)

    def action_confirm(self):
        for order in self:
            if order.partner_id.sale_blocked:
                raise ValidationError(_("Dieser Kunde ist für den Verkauf gesperrt und kann nicht bestätigt werden."))
            order.order_line._check_strict_pricelist_lock()
        return super().action_confirm()


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    def _is_strict_lock_ready(self):
        self.ensure_one()
        return bool(
            self.order_id
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

    def _get_matching_pricelist_items(self):
        self.ensure_one()
        if not self._is_strict_lock_ready():
            return self.env['product.pricelist.item']

        order = self.order_id
        pricelist = order.pricelist_id
        product = self.product_id
        if not pricelist:
            return self.env['product.pricelist.item']

        quantity = self.product_uom_qty or 1.0
        date = order.date_order.date() if order.date_order else fields.Date.context_today(self)
        partner = order.partner_id
        company = order.company_id

        domain = [
            ('pricelist_id', '=', pricelist.id),
            '|', ('company_id', '=', False), ('company_id', '=', company.id),
            '|', ('date_start', '=', False), ('date_start', '<=', date),
            '|', ('date_end', '=', False), ('date_end', '>=', date),
            '|', ('min_quantity', '=', False), ('min_quantity', '<=', quantity),
        ]

        items = self.env['product.pricelist.item'].search(domain)
        if hasattr(items, '_filter_applicable_rules'):
            items = items._filter_applicable_rules(product, quantity, partner)
        else:
            items = items.filtered(
                lambda item: (
                    item.applied_on == '3_global'
                    or (item.applied_on == '2_product_category' and product.categ_id and item.categ_id == product.categ_id)
                    or (item.applied_on == '1_product' and item.product_tmpl_id == product.product_tmpl_id)
                    or (item.applied_on == '0_product_variant' and item.product_id == product)
                )
            )
        return items

    def _is_allowed_strict_pricelist_item(self, item):
        self.ensure_one()
        if not item or item.compute_price != 'fixed':
            return False
        if item.applied_on == '0_product_variant':
            return item.product_id == self.product_id
        if item.applied_on == '1_product':
            return item.product_tmpl_id == self.product_id.product_tmpl_id
        return False

    def _get_product_locked_pricelist_item(self):
        self.ensure_one()
        if not self._should_apply_strict_lock():
            return self.env['product.pricelist.item']

        allowed_items = self._get_matching_pricelist_items().filtered(
            lambda item: self._is_allowed_strict_pricelist_item(item)
        )
        if not allowed_items:
            return self.env['product.pricelist.item']

        def priority_key(item):
            applied_on_rank = {
                '0_product_variant': 0,
                '1_product': 1,
                '2_product_category': 2,
                '3_global': 3,
            }
            return (
                applied_on_rank.get(item.applied_on, 99),
                -(item.min_quantity or 0.0),
                item.id,
            )

        return allowed_items.sorted(key=priority_key)[:1]

    def _get_locked_base_price(self):
        self.ensure_one()
        item = self._get_product_locked_pricelist_item()
        return item.fixed_price if item else None

    def _apply_locked_price(self):
        if self.env.context.get('skip_strict_pricelist_lock'):
            return

        for line in self:
            if not line._should_apply_strict_lock():
                continue

            locked_price = line._get_locked_base_price()
            if locked_price is None:
                continue

            rounding = line.currency_id.rounding if line.currency_id else 0.01
            if isclose(line.price_unit, locked_price, rel_tol=0.0, abs_tol=rounding):
                continue

            line.with_context(skip_strict_pricelist_lock=True).write({
                'price_unit': locked_price,
            })

    def _check_strict_pricelist_lock(self):
        if self.env.context.get('skip_strict_pricelist_lock'):
            return

        for line in self:
            if not line._should_apply_strict_lock():
                continue

            item = line._get_product_locked_pricelist_item()
            if not item:
                raise ValidationError(_(
                    "Für das Produkt '%s' ist die Rabattfähigkeit deaktiviert. "
                    "Es muss eine produkt- oder variantenbezogene Festpreis-Regel in der aktiven Preisliste vorhanden sein."
                ) % line.product_id.display_name)

            locked_price = item.fixed_price
            rounding = line.currency_id.rounding if line.currency_id else 0.01

            if not isclose(line.price_unit, locked_price, rel_tol=0.0, abs_tol=rounding):
                raise ValidationError(_(
                    "Für das Produkt '%s' ist die Rabattfähigkeit deaktiviert. "
                    "Der Artikelpreis muss aus der produktbezogenen Preislistenregel stammen (%s). "
                    "Zusätzlicher Positionsrabatt ist erlaubt, aber keine weitere Preislisten- oder Preisänderungslogik auf den Artikelpreis."
                ) % (line.product_id.display_name, locked_price))

    @api.model_create_multi
    def create(self, vals_list):
        lines = super().create(vals_list)
        if not self.env.context.get('skip_strict_pricelist_lock'):
            lines._apply_locked_price()
            lines._check_strict_pricelist_lock()
        return lines

    def write(self, vals):
        res = super().write(vals)
        if self.env.context.get('skip_strict_pricelist_lock'):
            return res

        if 'discount' not in vals:
            self._apply_locked_price()

        self._check_strict_pricelist_lock()
        return res

    @api.onchange('product_id', 'product_uom_id', 'product_uom_qty', 'price_unit', 'order_id.pricelist_id')
    def _onchange_strict_pricelist_lock(self):
        if self.env.context.get('skip_strict_pricelist_lock'):
            return

        for line in self:
            if not line._should_apply_strict_lock():
                continue
            line._apply_locked_price()
            line._check_strict_pricelist_lock()
