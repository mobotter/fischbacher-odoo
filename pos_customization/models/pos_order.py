# -*- coding: utf-8 -*-

from odoo import fields, models


class PosOrder(models.Model):
    _inherit = "pos.order"

    is_rental_order = fields.Boolean(
        string="Mietvorgang",
        readonly=True,
        copy=False,
        help=(
            "Wird automatisch gesetzt, wenn der POS-Auftrag mindestens "
            "eine Position mit einem als Mietartikel gekennzeichneten "
            "Produkt enthält."
        ),
    )

    def _load_pos_data_fields(self, config_id):
        field_names = super()._load_pos_data_fields(config_id)

        if "is_rental_order" not in field_names:
            field_names.append("is_rental_order")

        return field_names
