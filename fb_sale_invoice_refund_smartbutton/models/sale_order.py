from odoo import _, api, fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    fb_invoice_refund_ids = fields.Many2many(
        comodel_name="account.move",
        compute="_compute_fb_invoice_refund_ids",
        string="Rechnungen und Stornogutschriften",
    )
    fb_invoice_refund_count = fields.Integer(
        compute="_compute_fb_invoice_refund_ids",
        string="Rechnungen / Gutschriften",
    )

    @api.depends(
        "invoice_ids",
        "invoice_ids.move_type",
        "invoice_ids.reversal_move_ids",
        "invoice_ids.reversal_move_ids.move_type",
    )
    def _compute_fb_invoice_refund_ids(self):
        original_invoices = self.mapped("invoice_ids").filtered(
            lambda move: move.move_type == "out_invoice"
        )
        refunds = self.env["account.move"].search([
            ("move_type", "=", "out_refund"),
            ("reversed_entry_id", "in", original_invoices.ids),
        ]) if original_invoices else self.env["account.move"]
        refunds_by_invoice = {}
        for refund in refunds:
            invoice_id = refund.reversed_entry_id.id
            refunds_by_invoice.setdefault(invoice_id, self.env["account.move"])
            refunds_by_invoice[invoice_id] |= refund
        for order in self:
            moves = order.invoice_ids
            for invoice in order.invoice_ids:
                moves |= refunds_by_invoice.get(invoice.id, self.env["account.move"])
            order.fb_invoice_refund_ids = moves
            order.fb_invoice_refund_count = len(moves)

    def action_fb_view_invoices_and_refunds(self):
        self.ensure_one()
        moves = self.fb_invoice_refund_ids
        # Keep access rules in effect and do not inherit invoice-only search filters.
        context = dict(self.env.context)
        for key in list(context):
            if key.startswith("search_default_"):
                context.pop(key)
        context.update(default_move_type="out_invoice")
        action = {
            "type": "ir.actions.act_window",
            "name": _("Invoices and Credit Notes"),
            "res_model": "account.move",
            "view_mode": "list,form",
            "views": [(False, "list"), (False, "form")],
            "domain": [("id", "in", moves.ids)],
            "context": context,
            "target": "current",
        }
        if len(moves) == 1:
            action.update(
                view_mode="form",
                views=[(False, "form")],
                res_id=moves.id,
            )
        return action
