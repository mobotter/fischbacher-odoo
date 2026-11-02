from odoo import api, models
from odoo.exceptions import UserError


class SaleOrder(models.Model):
    _inherit = "sale.order"

    _EU_COUNTRY_CODES = frozenset({
        "AT", "BE", "BG", "HR", "CY", "CZ", "DK", "EE", "ES",
        "FI", "FR", "GR", "HU", "IE", "IT", "LT", "LU", "LV",
        "MT", "NL", "PL", "PT", "RO", "SE", "SI", "SK",
    })

    _SERVICE_FISCAL_POSITION_XMLID = (
        "account.1_fiscal_position_eu_vat_id_partner_service_skr04"
    )
    _GOODS_FISCAL_POSITION_XMLID = (
        "account.1_fiscal_position_eu_vat_id_partner_skr04"
    )

    def _fischbacher_is_foreign_eu_b2b(self):
        self.ensure_one()
        partner = self.partner_id.commercial_partner_id
        company_country = self.company_id.account_fiscal_country_id

        return bool(
            partner
            and partner.is_company
            and partner.country_id
            and company_country
            and partner.country_id.code in self._EU_COUNTRY_CODES
            and partner.country_id != company_country
            and partner.vat
        )

    def _fischbacher_get_fiscal_position(self):
        self.ensure_one()

        if not self._fischbacher_is_foreign_eu_b2b():
            return self.env["account.fiscal.position"]

        xmlid = (
            self._SERVICE_FISCAL_POSITION_XMLID
            if self.is_subscription
            else self._GOODS_FISCAL_POSITION_XMLID
        )
        position = self.env.ref(xmlid, raise_if_not_found=False)
        if not position:
            raise UserError(
                "Die Steuerposition mit der XML-ID %s wurde nicht gefunden."
                % xmlid
            )
        if position.company_id and position.company_id != self.company_id:
            raise UserError(
                "Die Steuerposition %s gehört zu einer anderen Gesellschaft."
                % position.display_name
            )
        return position

    def _fischbacher_apply_fiscal_position(self):
        for order in self:
            if order.state not in ("draft", "sent"):
                continue
            order.fiscal_position_id = order._fischbacher_get_fiscal_position()
        return True

    @api.onchange("is_subscription", "partner_id", "company_id")
    def _onchange_fischbacher_fiscal_position(self):
        self._fischbacher_apply_fiscal_position()

    @api.model_create_multi
    def create(self, vals_list):
        orders = super().create(vals_list)
        orders._fischbacher_apply_fiscal_position()
        return orders

    def write(self, vals):
        result = super().write(vals)
        if {"is_subscription", "partner_id", "company_id"} & set(vals):
            self._fischbacher_apply_fiscal_position()
        return result

    def action_confirm(self):
        self._fischbacher_check_line_types()
        self._fischbacher_apply_fiscal_position()
        return super().action_confirm()

    def _fischbacher_check_line_types(self):
        for order in self:
            if not order._fischbacher_is_foreign_eu_b2b():
                continue

            # Versandkostenzeilen werden nicht als Waren- oder
            # Leistungspositionen geprüft.
            lines = order.order_line.filtered(
                lambda line: (
                    line.product_id
                    and not getattr(line, "is_delivery", False)
                )
            )

            service_lines = lines.filtered(
                lambda line: (
                    getattr(line.product_id, "detailed_type", False)
                    or getattr(line.product_id, "type", False)
                ) == "service"
            )
            goods_lines = lines - service_lines

            if order.is_subscription and goods_lines:
                raise UserError(
                    "Ein Abonnement darf nur Leistungspositionen enthalten."
                )

            if not order.is_subscription and service_lines:
                raise UserError(
                    "Ein normaler Verkaufsauftrag darf nur Warenpositionen "
                    "enthalten."
                )
