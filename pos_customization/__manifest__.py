# -*- coding: utf-8 -*-
{
    "name": "Point of Sale Customizations",
    "version": "19.0.1.0.6",
    "category": "Sales/Point of Sale",
    "sequence": 40,
    "author": "Moritz Kern",
    "summary": "POS customizations and delivery validation after invoice settlement",
    "depends": [
        "point_of_sale",
        "sale_renting",
        "sale_stock",
        "web",
    ],
    "data": [],
    "assets": {
        "point_of_sale._assets_pos": [
            "pos_customization/static/src/js/pos.js",
            "pos_customization/static/src/js/double_print.js",

            "pos_customization/static/src/xml/pos_button.xml",
            "pos_customization/static/src/xml/product_card.xml",
            "pos_customization/static/src/xml/pos_receipt_transaction_type.xml",
            "pos_customization/static/src/xml/pos_receipt_default_code.xml",

            "pos_customization/static/src/css/pos_custom.css",
            "pos_customization/static/src/css/pos_font_fix.css",
        ],
    },
    "installable": True,
    "application": True,
    "license": "LGPL-3",
}
