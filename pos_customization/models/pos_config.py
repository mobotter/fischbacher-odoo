# -*- coding: utf-8 -*-

from odoo import fields, models


class PosConfig(models.Model):
    _inherit = "pos.config"

    allow_open_invoice_settlement = fields.Boolean(
        string="Offene Rechnungen im POS kassieren",
        help=(
            "Erlaubt das Anzeigen offener Kundenrechnungen im POS und "
            "deren Bezahlung über POS-Zahlungsmethoden."
        ),
        default=True,
    )
