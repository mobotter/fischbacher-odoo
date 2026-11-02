# Copyright (c) 2026 Moritz Kern, Fischbacher GmbH + Co. KG
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.html)

from odoo import _, api, fields, models
from odoo.exceptions import UserError

from ..models.sale_order_line import INTERNAL_WRITE_KEY


class CustomerOfferPriceWizard(models.TransientModel):
    _name = "customer.offer.price.wizard"
    _description = "Günstigerer Preis aus Kundenangebot"

    order_line_id = fields.Many2one(
        comodel_name="sale.order.line",
        string="Aktuelle Angebotszeile",
        required=True,
        readonly=True,
        ondelete="cascade",
    )

    source_line_id = fields.Many2one(
        comodel_name="sale.order.line",
        string="Quellangebotszeile",
        required=True,
        readonly=True,
        ondelete="cascade",
    )

    product_id = fields.Many2one(
        related="order_line_id.product_id",
        string="Produkt",
    )

    product_uom_id = fields.Many2one(
        related="order_line_id.product_uom_id",
        string="Einheit",
    )

    customer_id = fields.Many2one(
        related="order_line_id.order_id.partner_id",
        string="Kunde",
    )

    currency_id = fields.Many2one(
        related="order_line_id.order_id.currency_id",
        string="Währung",
    )

    current_price = fields.Monetary(
        string="Aktueller effektiver Preis",
        compute="_compute_prices",
        currency_field="currency_id",
    )

    cheaper_price = fields.Monetary(
        string="Günstigerer effektiver Preis",
        compute="_compute_prices",
        currency_field="currency_id",
    )

    price_difference = fields.Monetary(
        string="Ersparnis pro Einheit",
        compute="_compute_prices",
        currency_field="currency_id",
    )

    source_order_id = fields.Many2one(
        related="source_line_id.order_id",
        string="Quellangebot",
    )

    source_order_date = fields.Datetime(
        related="source_line_id.order_id.date_order",
        string="Angebotsdatum",
    )

    source_create_date = fields.Datetime(
        related="source_line_id.order_id.create_date",
        string="Erstellt am",
    )

    source_validity_date = fields.Date(
        related="source_line_id.order_id.validity_date",
        string="Gültig bis",
    )

    source_state = fields.Selection(
        related="source_line_id.order_id.state",
        string="Status",
    )

    source_quantity = fields.Float(
        related="source_line_id.product_uom_qty",
        string="Menge im Quellangebot",
    )

    source_discount = fields.Float(
        related="source_line_id.discount",
        string="Rabatt im Quellangebot (%)",
    )

    source_price_subtotal = fields.Monetary(
        related="source_line_id.price_subtotal",
        string="Zeilensumme im Quellangebot",
        currency_field="currency_id",
    )

    @api.depends(
        "order_line_id.price_unit",
        "order_line_id.discount",
        "order_line_id.fixed_price",
        "order_line_id.fixed_price_value",
        "source_line_id.price_unit",
        "source_line_id.discount",
        "source_line_id.fixed_price",
        "source_line_id.fixed_price_value",
    )
    def _compute_prices(self):
        for wizard in self:
            current_price = (
                wizard.order_line_id._get_effective_unit_price()
                if wizard.order_line_id
                else 0.0
            )
            cheaper_price = (
                wizard.source_line_id._get_effective_unit_price()
                if wizard.source_line_id
                else 0.0
            )

            wizard.current_price = current_price
            wizard.cheaper_price = cheaper_price
            wizard.price_difference = current_price - cheaper_price

    def _validate_offer_lines(self):
        """Validiert Ziel und Quelle unmittelbar vor der Übernahme."""
        self.ensure_one()

        target_line = self.order_line_id.exists()
        source_line = self.source_line_id.exists()

        if not target_line:
            raise UserError(
                _("Die aktuelle Angebotszeile ist nicht mehr vorhanden.")
            )

        if not source_line:
            raise UserError(_("Die Preisquelle ist nicht mehr vorhanden."))

        if not target_line._is_open_valid_customer_offer():
            raise UserError(_(
                "Die Preisübernahme ist nur in einem offenen und "
                "gültigen Angebot möglich."
            ))

        if not source_line._is_open_valid_customer_offer():
            raise UserError(_(
                "Das Quellangebot ist nicht mehr offen oder nicht "
                "mehr gültig. Bitte führen Sie die Suche erneut aus."
            ))

        if target_line == source_line:
            raise UserError(
                _("Die Angebotszeile kann nicht ihre eigene Preisquelle sein.")
            )

        target_order = target_line.order_id
        source_order = source_line.order_id

        if target_order == source_order:
            raise UserError(_(
                "Die Preisquelle muss aus einem anderen Angebot stammen."
            ))

        if target_line.display_type or source_line.display_type:
            raise UserError(_(
                "Der Preisvergleich ist nur für normale "
                "Produktpositionen möglich."
            ))

        if target_line.product_id != source_line.product_id:
            raise UserError(_(
                "Das Produkt der Quellposition stimmt nicht mehr "
                "mit dem Produkt der Zielposition überein."
            ))

        if target_line.product_uom_id != source_line.product_uom_id:
            raise UserError(_(
                "Quell- und Zielposition verwenden unterschiedliche "
                "Mengeneinheiten."
            ))

        if target_order.company_id != source_order.company_id:
            raise UserError(_(
                "Quell- und Zielangebot gehören nicht zur selben "
                "Gesellschaft."
            ))

        if target_order.currency_id != source_order.currency_id:
            raise UserError(_(
                "Quell- und Zielangebot verwenden unterschiedliche "
                "Währungen."
            ))

        target_partner = target_order.partner_id.commercial_partner_id
        source_partner = source_order.partner_id.commercial_partner_id

        if target_partner != source_partner:
            raise UserError(_(
                "Quell- und Zielangebot gehören nicht zum selben "
                "kommerziellen Kunden."
            ))

        return target_line, source_line

    def action_accept(self):
        """Übernimmt den effektiven Preis als nicht rabattierbaren Festpreis."""
        self.ensure_one()

        target_line, source_line = self._validate_offer_lines()

        source_price = source_line._get_effective_unit_price()
        target_price = target_line._get_effective_unit_price()

        if target_line._customer_offer_price_compare(source_price, 0.0) <= 0:
            raise UserError(
                _("Die Preisquelle enthält keinen gültigen positiven Preis.")
            )

        if target_line._customer_offer_price_compare(
            source_price, target_price
        ) >= 0:
            raise UserError(_(
                "Der Preis des Quellangebots ist nicht mehr günstiger. "
                "Bitte führen Sie die Suche erneut aus."
            ))

        target_line.with_context(**{INTERNAL_WRITE_KEY: True}).write(
            target_line._prepare_fixed_price_vals(
                source_price,
                source="wizard",
                source_line=source_line,
            )
        )

        return {"type": "ir.actions.act_window_close"}
