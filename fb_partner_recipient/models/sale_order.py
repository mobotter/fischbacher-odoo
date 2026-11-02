from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    partner_recipient_id = fields.Many2one(
        comodel_name="res.partner",
        string="Service Recipient",
        compute="_compute_partner_recipient_id",
        store=True,
        readonly=False,
        precompute=True,
        tracking=True,
        check_company=True,
        index="btree_not_null",
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]",
    )

    # Hilfsfelder für die Formularansicht: Gibt es beim Kunden untergeordnete
    # Kontakte der jeweiligen Adressart? Nur dann wird das Dropdown angezeigt.
    fb_commercial_partner_id = fields.Many2one(
        comodel_name="res.partner",
        string="Commercial Entity",
        related="partner_id.commercial_partner_id",
    )
    fb_has_invoice_address = fields.Boolean(
        string="Has Invoice Addresses",
        compute="_compute_fb_address_availability",
    )
    fb_has_delivery_address = fields.Boolean(
        string="Has Delivery Addresses",
        compute="_compute_fb_address_availability",
    )
    fb_has_recipient_address = fields.Boolean(
        string="Has Service Recipients",
        compute="_compute_fb_address_availability",
    )

    @api.depends("partner_id", "company_id")
    def _compute_fb_address_availability(self):
        Partner = self.env["res.partner"]
        for order in self:
            commercial = order.partner_id.commercial_partner_id
            types = set()
            if commercial:
                children = Partner.search([
                    ("id", "child_of", commercial.id),
                    ("id", "!=", commercial.id),
                    ("type", "in", ("invoice", "delivery", "recipient")),
                    "|",
                    ("company_id", "=", False),
                    ("company_id", "=", order.company_id.id),
                ])
                types = set(children.mapped("type"))
            order.fb_has_invoice_address = "invoice" in types
            order.fb_has_delivery_address = "delivery" in types
            order.fb_has_recipient_address = "recipient" in types

    @api.depends("partner_id")
    def _compute_partner_recipient_id(self):
        for order in self:
            order.partner_recipient_id = (
                order.partner_id._get_recipient_address() if order.partner_id else False
            )

    def _prepare_invoice(self):
        vals = super()._prepare_invoice()
        vals["partner_recipient_id"] = self.partner_recipient_id.id
        return vals

    def write(self, vals):
        res = super().write(vals)
        # Änderung am Auftrag auf offene Lieferscheine übertragen
        if "partner_recipient_id" in vals:
            for order in self:
                pickings = order.picking_ids.filtered(
                    lambda p: p.state not in ("done", "cancel")
                )
                if pickings:
                    pickings.partner_recipient_id = order.partner_recipient_id
        return res
