from math import isclose

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class SaleOrder(models.Model):
    _inherit = "sale.order"

    partner_id = fields.Many2one(
        "res.partner",
        string="Customer",
        required=True,
        change_default=True,
        index=True,
        tracking=1,
        domain=(
            "[('sale_blocked', '=', False), "
            "('customer_rank', '>', 0), "
            "('parent_id', '=', False)]"
        ),
    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            partner_id = vals.get("partner_id")

            if not partner_id:
                continue

            partner = self.env["res.partner"].browse(partner_id)

            if partner.exists() and partner.sale_blocked:
                raise UserError(
                    _("Dieser Kunde ist für den Verkauf gesperrt.")
                )

        return super().create(vals_list)

    def write(self, vals):
        if vals.get("partner_id"):
            partner = self.env["res.partner"].browse(
                vals["partner_id"]
            )

            if partner.exists() and partner.sale_blocked:
                raise UserError(
                    _("Dieser Kunde ist für den Verkauf gesperrt.")
                )

        result = super().write(vals)

        if self.env.context.get("skip_product_pricelist_only"):
            return result

        if "pricelist_id" in vals:
            for order in self.exists():
                locked_lines = order.order_line.exists().filtered(
                    lambda line: line._should_use_only_product_pricelist()
                )
                normal_lines = order.order_line.exists() - locked_lines

                # Produktpreislisten-Pflichtpreise werden auch bei einer
                # Preislistenänderung bewusst durchgesetzt.
                locked_lines._enforce_product_pricelist_only()

                # Manuell geänderte Einzelpreise werden nicht überschrieben.
                normal_lines._apply_standard_pricelist_price()

        return result

    def action_confirm(self):
        for order in self.exists():
            if (
                order.partner_id.exists()
                and order.partner_id.sale_blocked
            ):
                raise UserError(
                    _(
                        "Dieser Kunde ist für den Verkauf gesperrt und "
                        "kann nicht bestätigt werden."
                    )
                )

            locked_lines = order.order_line.exists().filtered(
                lambda line: line._should_use_only_product_pricelist()
            )

            # Fachliche Ausnahme: Produkte mit gesetztem
            # use_only_product_pricelist werden beim Bestätigen weiterhin
            # auf den vorgegebenen Produktpreis gesetzt.
            locked_lines._enforce_product_pricelist_only()

        return super().action_confirm()

    @api.onchange("pricelist_id")
    def _onchange_pricelist_id_reapply_line_prices(self):
        if self.env.context.get("skip_product_pricelist_only"):
            return

        for order in self.exists():
            locked_lines = order.order_line.exists().filtered(
                lambda line: line._should_use_only_product_pricelist()
            )
            normal_lines = order.order_line.exists() - locked_lines

            locked_lines._enforce_product_pricelist_only()
            normal_lines._apply_standard_pricelist_price()


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    def _is_product_pricelist_ready(self):
        self.ensure_one()

        return bool(
            self.exists()
            and self.order_id
            and self.product_id
            and self.product_uom_id
            and not self.display_type
        )

    def _has_manual_price(self):
        """
        Prüft den Odoo-19-Standardmarker für einen manuell geänderten Preis.

        Odoo setzt bei einer Preislistenberechnung normalerweise beide Werte
        identisch:

            technical_price_unit == price_unit

        Nach einer manuellen Änderung bleibt `technical_price_unit` der
        Preislistenpreis, während `price_unit` der vom Benutzer gewählte
        Preis ist. Bei einer Differenz darf kein Custom-Code `price_unit`
        neu aus der Preisliste setzen.
        """
        self.ensure_one()

        currency = (
            self.currency_id
            or self.company_id.currency_id
            or self.env.company.currency_id
        )

        return bool(
            currency.compare_amounts(
                self.technical_price_unit,
                self.price_unit,
            )
        )

    def _product_uses_only_product_pricelist(self):
        self.ensure_one()

        return bool(
            self.exists()
            and self.product_id.exists()
            and self.product_id.product_tmpl_id.exists()
            and self.product_id.product_tmpl_id.use_only_product_pricelist
        )

    def _should_use_only_product_pricelist(self):
        self.ensure_one()

        return bool(
            self._is_product_pricelist_ready()
            and self._product_uses_only_product_pricelist()
        )

    def _get_product_scoped_pricelist_items(self):
        self.ensure_one()

        if not self._should_use_only_product_pricelist():
            return self.env["product.pricelist.item"]

        order = self.order_id
        product = self.product_id
        quantity = self.product_uom_qty or 1.0
        date = (
            order.date_order.date()
            if order and order.date_order
            else fields.Date.context_today(self)
        )
        company = order.company_id if order else self.env.company

        domain = [
            ("applied_on", "in", ["0_product_variant", "1_product"]),
            "|",
            ("company_id", "=", False),
            ("company_id", "=", company.id),
            "|",
            ("date_start", "=", False),
            ("date_start", "<=", date),
            "|",
            ("date_end", "=", False),
            ("date_end", ">=", date),
            ("min_quantity", "<=", quantity),
        ]

        items = self.env["product.pricelist.item"].search(domain).exists()

        return items.filtered(
            lambda item: item.exists()
            and (
                (
                    item.applied_on == "0_product_variant"
                    and item.product_id == product
                )
                or (
                    item.applied_on == "1_product"
                    and item.product_tmpl_id
                    == product.product_tmpl_id
                )
            )
        )

    def _get_selected_product_pricelist_item(self):
        self.ensure_one()

        items = self._get_product_scoped_pricelist_items().exists()

        if not items:
            return self.env["product.pricelist.item"]

        def priority_key(item):
            return (
                0 if item.applied_on == "0_product_variant" else 1,
                -(item.min_quantity or 0.0),
                item.sequence,
                item.id,
            )

        return items.sorted(key=priority_key)[:1].exists()

    def _get_price_from_product_pricelist_rule(self):
        self.ensure_one()

        rule = self._get_selected_product_pricelist_item().exists()

        if not rule:
            return None

        product = self.product_id
        quantity = self.product_uom_qty or 1.0

        if not product.exists():
            return None

        if rule.compute_price == "fixed":
            return rule.fixed_price

        if rule.base == "list_price":
            base_price = product.lst_price
        elif rule.base == "standard_price":
            base_price = product.standard_price
        elif (
            rule.base == "pricelist"
            and rule.base_pricelist_id.exists()
        ):
            partner = (
                self.order_id.partner_id
                if self.order_id
                and self.order_id.partner_id.exists()
                else False
            )

            base_price = rule.base_pricelist_id._get_product_price(
                product,
                quantity,
                partner,
            )
        else:
            base_price = product.lst_price

        if rule.compute_price == "percentage":
            return base_price * (
                1 - (rule.percent_price or 0.0) / 100.0
            )

        if rule.compute_price == "formula":
            price = base_price

            if rule.price_discount:
                price = price * (1 - rule.price_discount)

            if rule.price_surcharge:
                price += rule.price_surcharge

            if rule.price_round:
                price = round(
                    price / rule.price_round
                ) * rule.price_round

            if rule.price_min_margin:
                price = max(
                    price,
                    base_price + rule.price_min_margin,
                )

            if rule.price_max_margin:
                price = min(
                    price,
                    base_price + rule.price_max_margin,
                )

            return price

        return base_price

    def _get_standard_pricelist_price(self):
        self.ensure_one()

        if not (
            self.order_id
            and self.order_id.pricelist_id
            and self.product_id
            and self.product_uom_id
        ):
            return None

        line = self.with_context(
            lang=(
                self.order_id.partner_id.lang
                if self.order_id.partner_id
                else False
            ),
            partner=(
                self.order_id.partner_id.id
                if self.order_id.partner_id
                else False
            ),
            quantity=self.product_uom_qty,
            date=self.order_id.date_order,
            pricelist=self.order_id.pricelist_id.id,
            uom=self.product_uom_id.id,
            fiscal_position=(
                self.order_id.fiscal_position_id.id
                if self.order_id.fiscal_position_id
                else False
            ),
        )

        return line._get_display_price()

    def _apply_standard_pricelist_price(self):
        """
        Aktualisiert den Preis nur bei automatisch bepreisten Zeilen.

        Ein manuell geänderter Odoo-19-Preis wird nie überschrieben.
        """
        if self.env.context.get("skip_product_pricelist_only"):
            return

        for line in self.exists():
            if not line._is_product_pricelist_ready():
                continue

            if line._should_use_only_product_pricelist():
                continue

            # Der entscheidende Fix:
            # Manuell eingegebener Preis bleibt bei Mengen-, UoM- und
            # Preislistenänderungen vollständig erhalten.
            if line._has_manual_price():
                continue

            price = line._get_standard_pricelist_price()

            if price is None:
                continue

            rounding = (
                line.currency_id.rounding
                if line.currency_id
                else 0.01
            )

            if isclose(
                line.price_unit,
                price,
                rel_tol=0.0,
                abs_tol=rounding,
            ):
                continue

            line.update({
                "price_unit": price,
                "technical_price_unit": price,
            })

    def _enforce_product_pricelist_only(self):
        """
        Setzt den Produktpreis für Produkte mit Preislisten-Pflicht.

        Diese Regel ist bewusst stärker als ein manueller Preis: Wenn
        `use_only_product_pricelist=True` gesetzt ist, soll der Preis
        fachlich zwingend aus der produktbezogenen Preislistenregel kommen.
        """
        if self.env.context.get("skip_product_pricelist_only"):
            return

        for line in self.exists():
            if not line._should_use_only_product_pricelist():
                continue

            target_price = line._get_price_from_product_pricelist_rule()

            if target_price is None:
                continue

            rounding = (
                line.currency_id.rounding
                if line.currency_id
                else 0.01
            )

            if isclose(
                line.price_unit,
                target_price,
                rel_tol=0.0,
                abs_tol=rounding,
            ):
                if line.discount:
                    line.update({
                        "discount": 0.0,
                    })
                continue

            line.update({
                "price_unit": target_price,
                "technical_price_unit": target_price,
                "discount": 0.0,
            })

    def _compute_price_unit(self):
        """
        Ergänzt den Odoo-Standard nur für Produkte mit Preislisten-Pflicht.

        `super()` enthält bereits Odoo 19s eigene Erkennung manueller Preise.
        Für normale Produkte erfolgt anschließend keine erneute eigene
        Berechnung durch dieses Modul.
        """
        super()._compute_price_unit()

        if self.env.context.get("skip_product_pricelist_only"):
            return

        valid_lines = self.exists().filtered(
            lambda line: line._is_product_pricelist_ready()
        )

        locked_lines = valid_lines.filtered(
            lambda line: line._should_use_only_product_pricelist()
        )

        locked_lines._enforce_product_pricelist_only()

    @api.model_create_multi
    def create(self, vals_list):
        lines = super().create(vals_list)

        if self.env.context.get("skip_product_pricelist_only"):
            return lines

        lines = lines.exists()

        locked_lines = lines.filtered(
            lambda line: line._should_use_only_product_pricelist()
        )
        normal_lines = lines - locked_lines

        locked_lines._enforce_product_pricelist_only()
        normal_lines._apply_standard_pricelist_price()

        return lines

    def write(self, vals):
        result = super().write(vals)

        if self.env.context.get("skip_product_pricelist_only"):
            return result

        trigger_fields = {
            "product_id",
            "product_uom_id",
            "product_uom_qty",
        }

        if trigger_fields.intersection(vals):
            lines = self.exists()

            locked_lines = lines.filtered(
                lambda line: line._should_use_only_product_pricelist()
            )
            normal_lines = lines - locked_lines

            locked_lines._enforce_product_pricelist_only()
            normal_lines._apply_standard_pricelist_price()

        return result

    @api.onchange(
        "product_id",
        "product_uom_id",
        "product_uom_qty",
    )
    def _onchange_product_pricelist_only(self):
        """
        Wendet die eigene Produktpreisregel nur auf nicht-manuelle Preise an.

        Der Standardpreis bleibt bei Mengenänderung für automatische Zeilen
        dynamisch; ein durch den Nutzer gesetzter Einzelpreis bleibt stehen.
        """
        if self.env.context.get("skip_product_pricelist_only"):
            return

        valid_lines = self.exists()

        locked_lines = valid_lines.filtered(
            lambda line: line._should_use_only_product_pricelist()
        )
        normal_lines = valid_lines - locked_lines

        locked_lines._enforce_product_pricelist_only()
        normal_lines._apply_standard_pricelist_price()
