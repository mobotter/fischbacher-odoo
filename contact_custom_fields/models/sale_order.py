from math import isclose

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from odoo.tools import float_compare


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

    def _product_has_strict_lock(self):
        self.ensure_one()
        return bool(self.product_id and self.product_id.product_tmpl_id.strict_pricelist_lock)

    def _get_matching_pricelist_items(self):
        self.ensure_one()
        order = self.order_id
        pricelist = order.pricelist_id
        product = self.product_id
        if not pricelist or not product:
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

    def _get_final_locked_pricelist_item(self):
        self.ensure_one()
        allowed_items = self._get_matching_pricelist_items().filtered(self._is_allowed_strict_pricelist_item)
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

    def _is_allowed_strict_pricelist_item(self, item):
        self.ensure_one()
        if not item:
            return False
        if item.compute_price != 'fixed':
            return False
        if item.applied_on == '0_product_variant':
            return item.product_id == self.product_id
        if item.applied_on == '1_product':
            return item.product_tmpl_id == self.product_id.product_tmpl_id
        return False

    def _get_locked_price_from_item(self, item):
        self.ensure_one()
        if not item:
            return None
        return item.fixed_price

    def _apply_locked_price(self):
        for line in self:
            if not line.product_id or line.display_type or not line._product_has_strict_lock():
                continue
            item = line._get_final_locked_pricelist_item()
            if not item:
                continue
            locked_price = line._get_locked_price_from_item(item)
            line.discount = 0.0
            line.price_unit = locked_price

    def _check_strict_pricelist_lock(self):
        for line in self:
            if not line.product_id or line.display_type:
                continue
            if not line._product_has_strict_lock():
                continue

            item = line._get_final_locked_pricelist_item()
            if not item:
                raise ValidationError(_(
                    "Für das Produkt '%s' ist eine strenge Preislisten-Sperre aktiv. "
                    "Es muss eine produkt- oder variantenbezogene Festpreis-Regel in der aktiven Preisliste vorhanden sein."
                ) % line.product_id.display_name)

            locked_price = line._get_locked_price_from_item(item)
            rounding = line.currency_id.rounding if line.currency_id else 0.01

            if float_compare(line.discount or 0.0, 0.0, precision_rounding=rounding) != 0:
                raise ValidationError(_(
                    "Für das Produkt '%s' ist eine strenge Preislisten-Sperre aktiv. Zusätzliche Rabatte sind nicht erlaubt."
                ) % line.product_id.display_name)

            if not isclose(line.price_unit, locked_price, rel_tol=0.0, abs_tol=rounding):
                raise ValidationError(_(
                    "Für das Produkt '%s' ist eine strenge Preislisten-Sperre aktiv. "
                    "Der Preis muss exakt dem Produkt-Sonderpreis aus der Preislistenregel entsprechen (%s)."
                ) % (line.product_id.display_name, locked_price))

    @api.model_create_multi
    def create(self, vals_list):
        lines = super().create(vals_list)
        lines._apply_locked_price()
        lines._check_strict_pricelist_lock()
        return lines

    def write(self, vals):
        res = super().write(vals)
        self._apply_locked_price()
        self._check_strict_pricelist_lock()
        return res

    @api.onchange('product_id', 'product_uom_qty', 'discount', 'price_unit', 'order_id.pricelist_id')
    def _onchange_strict_pricelist_lock(self):
        for line in self:
            if not line.product_id or line.display_type or not line._product_has_strict_lock():
                continue
            line._apply_locked_price()
            line._check_strict_pricelist_lock()
