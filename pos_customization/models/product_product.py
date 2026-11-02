# -*- coding: utf-8 -*-

from odoo import fields, models


class ProductProduct(models.Model):
    _inherit = "product.product"

    pos_rent_ok = fields.Boolean(
        string="Mietartikel im POS",
        related="product_tmpl_id.rent_ok",
        readonly=True,
    )

    def _load_pos_data_fields(self, config_id):
        field_names = super()._load_pos_data_fields(config_id)

        for field_name in ("default_code", "pos_rent_ok"):
            if field_name not in field_names:
                field_names.append(field_name)

        return field_names
