# Copyright (c) 2026 Moritz Kern, Fischbacher GmbH + Co. KG
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.html)

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools import float_compare, float_is_zero, float_round

#: Context-Schalter ausschließlich für den Schreibvorgang des Wizards.
INTERNAL_WRITE_KEY = "customer_offer_price_internal_write"


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    price_source = fields.Selection(
        selection=[
            ("auto", "Automatisch (Preisliste)"),
            ("wizard", "Festpreis aus Kundenangebot"),
            ("manual", "Manuell geänderter Preis"),
        ],
        string="Preisquelle",
        default="auto",
        readonly=True,
        copy=False,
    )

    fixed_price = fields.Boolean(
        string="Festpreis",
        default=False,
        readonly=True,
        copy=False,
        help=(
            "Der manuell geänderte oder aus einem Kundenangebot übernommene "
            "Einzelpreis wird bei Mengenänderungen nicht aus der Preisliste "
            "neu bestimmt. Ein zusätzlicher Rabatt ist nur bei manuell "
            "geänderten Preisen zulässig."
        ),
    )

    fixed_price_value = fields.Float(
        string="Festpreiswert",
        readonly=True,
        copy=False,
        digits="Product Price",
        help=(
            "Gespeicherter Einzelpreis eines manuellen oder aus einem "
            "Kundenangebot übernommenen Festpreises."
        ),
    )

    price_source_line_id = fields.Many2one(
        comodel_name="sale.order.line",
        string="Festpreis übernommen aus",
        readonly=True,
        copy=False,
        index="btree_not_null",
        ondelete="set null",
    )

    # Nicht gespeichert: wird bei jedem Laden und in jedem Onchange neu
    # ermittelt. Dadurch bleibt der Button "Preis prüfen" auch nach dem
    # Speichern bzw. Neuladen des Angebots korrekt sichtbar.
    has_cheaper_customer_offer = fields.Boolean(
        string="Günstigerer Kundenpreis vorhanden",
        compute="_compute_cheaper_customer_offer",
    )

    cheaper_customer_price = fields.Monetary(
        string="Günstigerer Kundenpreis",
        currency_field="currency_id",
        compute="_compute_cheaper_customer_offer",
    )

    cheaper_customer_offer_line_id = fields.Many2one(
        comodel_name="sale.order.line",
        string="Gefundenes Quellangebot",
        compute="_compute_cheaper_customer_offer",
    )

    # ------------------------------------------------------------------
    # Hilfsmethoden
    # ------------------------------------------------------------------

    def _customer_offer_price_digits(self):
        return self.env["decimal.precision"].precision_get("Product Price")

    def _customer_offer_price_compare(self, value1, value2):
        return float_compare(
            value1,
            value2,
            precision_digits=self._customer_offer_price_digits(),
        )

    def _is_open_valid_customer_offer(self):
        """True nur für offene und noch gültige Angebote."""
        self.ensure_one()

        order = self.order_id
        if not order or order.state not in ("draft", "sent") or order.locked:
            return False

        return (
            not order.validity_date
            or order.validity_date >= fields.Date.context_today(self)
        )

    def _is_protected_fixed_price(self):
        """True für vor Preislisten-Neuberechnung geschützte Einzelpreise."""
        self.ensure_one()

        return bool(
            self.fixed_price
            and self.price_source in ("manual", "wizard")
            and not self.display_type
            and self._is_open_valid_customer_offer()
        )

    def _is_discount_locked_customer_offer_price(self):
        """Nur der bereits effektive Wizard-Preis sperrt weitere Rabatte."""
        self.ensure_one()
        return self._is_protected_fixed_price() and self.price_source == "wizard"

    def _get_effective_unit_price(self):
        """Effektiver Netto-Einzelpreis, gerundet auf Product Price."""
        self.ensure_one()

        if self.fixed_price:
            price = self.fixed_price_value
        else:
            price = self.price_unit

        if self.price_source != "wizard":
            price *= 1.0 - (self.discount or 0.0) / 100.0

        return float_round(
            price,
            precision_digits=self._customer_offer_price_digits(),
        )

    def _prepare_fixed_price_vals(
        self, price, source="manual", source_line=False, discount=0.0
    ):
        return {
            "price_unit": price,
            "discount": 0.0 if source == "wizard" else discount,
            "fixed_price": True,
            "fixed_price_value": price,
            "price_source": source,
            "price_source_line_id": source_line.id if source_line else False,
        }

    def _prepare_reset_fixed_price_vals(self):
        return {
            "fixed_price": False,
            "fixed_price_value": 0.0,
            "price_source": "auto",
            "price_source_line_id": False,
        }

    # ------------------------------------------------------------------
    # Suche nach günstigeren Kundenangeboten
    # ------------------------------------------------------------------

    def _customer_offer_price_domain(self):
        """Suchdomain für andere offene und gültige Angebote desselben Kunden."""
        self.ensure_one()

        order = self.order_id
        if (
            self.display_type
            or not self.product_id
            or not self.product_uom_id
            or not order.partner_id
            or not self._is_open_valid_customer_offer()
        ):
            return [("id", "=", 0)]

        commercial_partner = order.partner_id.commercial_partner_id
        today = fields.Date.context_today(self)

        domain = [
            (
                "order_id.partner_id.commercial_partner_id",
                "=",
                commercial_partner.id,
            ),
            ("order_id.state", "in", ("draft", "sent")),
            ("order_id.locked", "=", False),
            ("order_id.company_id", "=", order.company_id.id),
            ("order_id.currency_id", "=", order.currency_id.id),
            ("product_id", "=", self.product_id.id),
            ("product_uom_id", "=", self.product_uom_id.id),
            ("display_type", "=", False),
            ("price_unit", ">", 0),
            "|",
            ("order_id.validity_date", "=", False),
            ("order_id.validity_date", ">=", today),
        ]

        if self._origin.id:
            domain.append(("id", "!=", self._origin.id))
        if order._origin.id:
            domain.append(("order_id", "!=", order._origin.id))

        return domain

    def _find_cheaper_customer_offer(self):
        """Günstigere Quellpositionen, aufsteigend nach effektivem Preis."""
        self.ensure_one()

        empty = self.env["sale.order.line"]
        if not self._is_open_valid_customer_offer():
            return empty

        current_price = self._get_effective_unit_price()
        if self._customer_offer_price_compare(current_price, 0.0) <= 0:
            return empty

        candidates = empty.search(self._customer_offer_price_domain())

        cheaper_lines = candidates.filtered(
            lambda line: self._customer_offer_price_compare(
                line._get_effective_unit_price(), current_price
            ) < 0
        )

        return cheaper_lines.sorted(
            key=lambda line: (line._get_effective_unit_price(), line.id)
        )

    @api.depends(
        "display_type",
        "product_id",
        "product_uom_id",
        "price_unit",
        "discount",
        "fixed_price",
        "fixed_price_value",
        "order_id.partner_id",
        "order_id.state",
        "order_id.locked",
        "order_id.validity_date",
        "order_id.company_id",
        "order_id.currency_id",
    )
    @api.depends_context("tz")
    def _compute_cheaper_customer_offer(self):
        for line in self:
            cheaper_line = line._find_cheaper_customer_offer()[:1]

            line.has_cheaper_customer_offer = bool(cheaper_line)
            line.cheaper_customer_offer_line_id = cheaper_line
            line.cheaper_customer_price = (
                cheaper_line._get_effective_unit_price()
                if cheaper_line
                else 0.0
            )

    # ------------------------------------------------------------------
    # Schutz des Einzelpreises bei automatischer Neuberechnung
    # ------------------------------------------------------------------

    def _compute_price_unit(self):
        """Manuelle und Wizard-Einzelpreise nicht neu berechnen."""
        protected = self.filtered(lambda line: line._is_protected_fixed_price())
        return super(SaleOrderLine, self - protected)._compute_price_unit()

    def _compute_discount(self):
        """Wizard-Preise rabattfrei halten; manuelle Rabatte bewahren."""
        protected = self.filtered(lambda line: line._is_protected_fixed_price())
        wizard_lines = protected.filtered(lambda line: line.price_source == "wizard")

        for line in wizard_lines:
            line.discount = 0.0

        # Weder Wizard- noch manuelle Festpreise an die Preislisten-
        # Rabattberechnung geben: manuell eingegebene Rabatte bleiben erhalten.
        return super(SaleOrderLine, self - protected)._compute_discount()

    # ------------------------------------------------------------------
    # Onchanges
    # ------------------------------------------------------------------

    @api.onchange("product_id", "product_uom_id")
    def _onchange_reset_fixed_price_on_product_or_uom(self):
        """Ein Festpreis gilt nur für Produkt und Mengeneinheit der Übernahme."""
        for line in self:
            if not line.fixed_price:
                continue
            if (
                line._origin
                and line._origin.product_id == line.product_id
                and line._origin.product_uom_id == line.product_uom_id
            ):
                continue
            line.update(line._prepare_reset_fixed_price_vals())

    @api.onchange("price_unit")
    def _onchange_mark_manual_price(self):
        """Einen tatsächlich manuell geänderten Preis markieren."""
        for line in self:
            if (
                line.display_type
                or not line.product_id
                or not line._is_open_valid_customer_offer()
            ):
                continue

            if line.fixed_price:
                if not line._customer_offer_price_compare(
                    line.price_unit, line.fixed_price_value
                ):
                    continue
            elif not line._customer_offer_price_compare(
                line.price_unit, line.technical_price_unit
            ):
                continue

            line.update(line._prepare_fixed_price_vals(
                line.price_unit,
                discount=line.discount,
            ))

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------

    @api.model_create_multi
    def create(self, vals_list):
        """Explizit markierte Festpreise beim Anlegen normalisieren."""
        prepared_vals_list = []

        for vals in vals_list:
            vals = dict(vals)

            if (
                not vals.get("display_type")
                and (
                    vals.get("fixed_price")
                    or vals.get("price_source") in ("manual", "wizard")
                )
            ):
                price = vals.get("fixed_price_value") or vals.get("price_unit", 0.0)
                source = vals.get("price_source")
                if source not in ("manual", "wizard"):
                    source = "manual"

                vals.update({
                    "price_unit": price,
                    "discount": 0.0 if source == "wizard" else vals.get("discount", 0.0),
                    "fixed_price": True,
                    "fixed_price_value": price,
                    "price_source": source,
                })
                if source == "manual":
                    vals["price_source_line_id"] = False

            prepared_vals_list.append(vals)

        return super().create(prepared_vals_list)

    def _prepare_fixed_price_line_write_vals(self, vals):
        """Schreibwerte für eine geschützte Festpreisposition anpassen."""
        self.ensure_one()

        line_vals = dict(vals)

        product_changed = (
            "product_id" in vals and vals["product_id"] != self.product_id.id
        )
        uom_changed = (
            "product_uom_id" in vals
            and vals["product_uom_id"] != self.product_uom_id.id
        )
        if product_changed or uom_changed:
            line_vals.update(self._prepare_reset_fixed_price_vals())
            return line_vals, True

        if self._is_discount_locked_customer_offer_price():
            discount_digits = self.env["decimal.precision"].precision_get("Discount")
            if "discount" in vals and not float_is_zero(
                vals["discount"] or 0.0,
                precision_digits=discount_digits,
            ):
                raise UserError(_(
                    "Für einen aus einem Kundenangebot übernommenen Preis "
                    "ist kein zusätzlicher Positionsrabatt zulässig "
                    "(Position: %(line)s).",
                    line=self.display_name,
                ))
            if "discount" in vals:
                line_vals["discount"] = 0.0

        if "price_unit" in vals and self._customer_offer_price_compare(
            vals["price_unit"], self.fixed_price_value
        ):
            # Manuelle Änderung des Wizard- oder manuellen Festpreises:
            # Preisquelle auf manual umstellen und Rabatt erhalten.
            line_vals.update(self._prepare_fixed_price_vals(
                vals["price_unit"],
                discount=vals.get("discount", self.discount),
            ))

        return line_vals, False

    def write(self, vals):
        """Wizard-Preise schützen und manuelle Einzelpreise erhalten."""
        tracked_fields = {"price_unit", "discount", "product_id", "product_uom_id"}

        if (
            self.env.context.get(INTERNAL_WRITE_KEY)
            or not tracked_fields & vals.keys()
        ):
            return super().write(vals)

        protected = self.filtered(lambda line: line._is_protected_fixed_price())
        if not protected:
            return super().write(vals)

        # Erst alles prüfen, dann schreiben: kein Teil-Schreiben bei Fehler.
        prepared = [
            (line, *line._prepare_fixed_price_line_write_vals(vals))
            for line in protected
        ]

        others = self - protected
        if others:
            super(SaleOrderLine, others).write(vals)

        reset_lines = self.browse()
        for line, line_vals, was_reset in prepared:
            super(SaleOrderLine, line).write(line_vals)
            if was_reset and "price_unit" not in vals:
                reset_lines |= line

        if reset_lines:
            reset_lines.with_context(
                force_price_recomputation=True
            )._compute_price_unit()
            reset_lines._compute_discount()

        return True

    # ------------------------------------------------------------------
    # Aktionen
    # ------------------------------------------------------------------

    def action_save_and_open_wizard(self):
        """Öffnet den Preisassistenten für eine Angebotsposition."""
        self.ensure_one()

        if not self._is_open_valid_customer_offer():
            raise UserError(_(
                "Die Preisübernahme ist nur in einem offenen und "
                "gültigen Angebot möglich."
            ))

        if not self.order_id.partner_id:
            raise UserError(_("Für das Angebot ist kein Kunde eingetragen."))

        if not self.product_id:
            raise UserError(
                _("Für diese Angebotszeile ist kein Produkt eingetragen.")
            )

        cheaper_line = self._find_cheaper_customer_offer()[:1]

        if not cheaper_line:
            raise UserError(_(
                "Für dieses Produkt wurde in gültigen, laufenden "
                "Angeboten dieses Kunden kein günstigerer Preis gefunden."
            ))

        wizard = self.env["customer.offer.price.wizard"].create({
            "order_line_id": self.id,
            "source_line_id": cheaper_line.id,
        })

        return {
            "type": "ir.actions.act_window",
            "name": _("Günstigerer Kundenpreis"),
            "res_model": "customer.offer.price.wizard",
            "view_mode": "form",
            "res_id": wizard.id,
            "target": "new",
        }
