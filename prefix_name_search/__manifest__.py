{
    "name": "Prefix Search Views",
    "version": "19.0.1.0.0",
    "author": "Moritz Kern",
    "summary": "Suchleisten in ausgewählten Odoo-Views auf begins with umstellen",
    "description": """
Dieses Modul erweitert die Search Views in Odoo 19 so, dass Benutzer
in ausgewählten Listenansichten mit Präfix-Suche statt Contains-Suche
arbeiten können. Es betrifft insbesondere Contacts und Produktansichten.
""",
    "depends": [
        "base",
        "product",
        "purchase",
        "stock",
        "sale_renting",
        "sale_subscription",
    ],
    "data": [
        "views/search_views.xml",
        "views/sale_order_views.xml",
    ],
    "installable": True,
    "application": False,
    "license": "LGPL-3",
}
