# -*- coding: utf-8 -*-

from odoo import _, api, models
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_compare, float_is_zero


class PosSession(models.Model):
    _inherit = "pos.session"

    @api.model
    def get_open_customer_invoices_for_pos(self, pos_config_id, search_term=None):
        pos_config = self.env["pos.config"].browse(pos_config_id).exists()
        if not pos_config:
            raise UserError(_("Die POS-Konfiguration wurde nicht gefunden."))

        if pos_config.company_id != self.env.company:
            raise UserError(_("Die angeforderte Kasse gehört zu einer anderen Gesellschaft."))

        if not pos_config.allow_open_invoice_settlement:
            return []

        domain = [
            ("company_id", "=", pos_config.company_id.id),
            ("move_type", "=", "out_invoice"),
            ("state", "=", "posted"),
            ("payment_state", "in", ("not_paid", "partial", "in_payment")),
            ("amount_residual", ">", 0),
        ]

        if search_term:
            domain += [
                "|",
                "|",
                "|",
                "|",
                ("name", "ilike", search_term),
                ("invoice_origin", "ilike", search_term),
                ("ref", "ilike", search_term),
                ("partner_id.name", "ilike", search_term),
                ("partner_id.ref", "ilike", search_term),
            ]

        invoices = self.env["account.move"].search(
            domain,
            order="invoice_date_due asc, invoice_date asc, id asc",
            limit=100,
        )

        return [{
            "id": invoice.id,
            "name": invoice.name,
            "invoice_origin": invoice.invoice_origin or "",
            "ref": invoice.ref or "",
            "partner_id": invoice.partner_id.id,
            "partner_name": invoice.partner_id.display_name,
            "partner_ref": invoice.partner_id.ref or "",
            "invoice_date": str(invoice.invoice_date or ""),
            "invoice_date_due": str(invoice.invoice_date_due or ""),
            "currency_id": invoice.currency_id.id,
            "currency_name": invoice.currency_id.name,
            "amount_total": invoice.amount_total,
            "amount_residual": invoice.amount_residual,
            "payment_state": invoice.payment_state,
        } for invoice in invoices]

    @api.model
    def settle_open_customer_invoice_from_pos(
        self,
        pos_session_id,
        invoice_id,
        payment_method_id,
        amount,
    ):
        session = self.browse(pos_session_id).exists()
        if not session:
            raise UserError(_("Die POS-Sitzung wurde nicht gefunden."))

        if session.state != "opened":
            raise UserError(_("Die POS-Sitzung ist nicht geöffnet."))

        config = session.config_id
        if not config.allow_open_invoice_settlement:
            raise UserError(_("Das Kassieren offener Rechnungen ist für diese Kasse deaktiviert."))

        invoice = self.env["account.move"].browse(invoice_id).exists()
        if not invoice:
            raise UserError(_("Die Rechnung wurde nicht gefunden."))

        if (
            invoice.company_id != config.company_id
            or invoice.move_type != "out_invoice"
            or invoice.state != "posted"
        ):
            raise ValidationError(_("Diese Rechnung kann an dieser Kasse nicht kassiert werden."))

        if invoice.payment_state == "paid" or float_is_zero(
            invoice.amount_residual,
            precision_rounding=invoice.currency_id.rounding,
        ):
            raise ValidationError(_("Die Rechnung ist bereits vollständig bezahlt."))

        payment_method = self.env["pos.payment.method"].browse(payment_method_id).exists()
        if not payment_method or payment_method not in config.payment_method_ids:
            raise ValidationError(_("Die gewählte Zahlungsmethode ist für diese Kasse nicht verfügbar."))

        try:
            amount = float(amount)
        except (TypeError, ValueError):
            raise ValidationError(_("Der Zahlungsbetrag ist ungültig."))

        if float_compare(
            amount,
            0.0,
            precision_rounding=invoice.currency_id.rounding,
        ) <= 0:
            raise ValidationError(_("Der Zahlungsbetrag muss größer als null sein."))

        if float_compare(
            amount,
            invoice.amount_residual,
            precision_rounding=invoice.currency_id.rounding,
        ) > 0:
            raise ValidationError(
                _("Der Zahlungsbetrag darf den offenen Rechnungsbetrag nicht überschreiten.")
            )

        payment_method_journal = payment_method.journal_id
        if not payment_method_journal:
            raise ValidationError(
                _("Die Zahlungsmethode '%s' besitzt kein Buchungsjournal.")
                % payment_method.display_name
            )

        payment = self.env["account.payment"].create({
            "payment_type": "inbound",
            "partner_type": "customer",
            "partner_id": invoice.partner_id.id,
            "amount": amount,
            "currency_id": invoice.currency_id.id,
            "date": self.env.context.get("pos_payment_date") or fields.Date.context_today(self),
            "journal_id": payment_method_journal.id,
            "ref": _("POS-Zahlung %s / Rechnung %s") % (session.name, invoice.name),
        })
        payment.action_post()

        receivable_lines = invoice.line_ids.filtered(
            lambda line: (
                line.account_id.account_type == "asset_receivable"
                and not line.reconciled
            )
        )
        payment_receivable_lines = payment.move_id.line_ids.filtered(
            lambda line: (
                line.account_id.account_type == "asset_receivable"
                and not line.reconciled
            )
        )

        lines_to_reconcile = receivable_lines + payment_receivable_lines
        if len(lines_to_reconcile.mapped("account_id")) != 1:
            raise ValidationError(
                _("Die Debitorenkonten von Rechnung und Zahlung stimmen nicht überein.")
            )

        lines_to_reconcile.reconcile()

        return {
            "invoice_id": invoice.id,
            "invoice_name": invoice.name,
            "partner_name": invoice.partner_id.display_name,
            "amount_paid": amount,
            "amount_residual": invoice.amount_residual,
            "payment_state": invoice.payment_state,
            "payment_id": payment.id,
            "payment_name": payment.name,
        }
