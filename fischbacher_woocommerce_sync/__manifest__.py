{
    "name": "Fischbacher WooCommerce Preis- und Bestandssync",
    "version": "19.0.1.0.0",
    "category": "Sales",
    "summary": "Synchronisiert Preis und Bestand von Odoo nach WooCommerce",
    "author": "Moritz Kern",
    "company": "Fischbacher GmbH + Co. KG",
    "license": "LGPL-3",
    "depends": ["product"],
    "data": [
        "views/product_template_views.xml",
        "views/res_config_settings_views.xml",
    ],
    "installable": True,
    "application": False,
}
