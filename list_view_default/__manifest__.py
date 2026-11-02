# -*- coding: utf-8 -*-

{
    "name": "List View Default",
    "version": "19.0.1.0.0",
    "category": "Tools",
    "summary": "Opens selected Odoo actions in list view by default",
    "description": """
List View Default
=================

Makes list views the default view for commonly used Odoo actions, including:

- Products
- Product variants
- Customers
- Stock products
- Stock product variants
- Rental products
- Subscription products
- Similar product and partner overviews

Kanban and form views remain available where supported.
    """,
    "author": "Moritz Kern",
    "license": "LGPL-3",
    "depends": [
        "product",
        "stock",
        "sale_management",
    ],
    "data": [
        "data/product_actions.xml",
        "data/partner_actions.xml",
    ],
    "installable": True,
    "application": False,
}
