# Copyright (c) 2026 Moritz Kern, Fischbacher GmbH + Co. KG
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.html)
{
    "name": "Global Quantity Discounts (Mengenstaffeln)",
    "version": "19.0.1.3.0",
    "category": "Sales",
    "author": "Moritz Kern, Fischbacher GmbH + Co. KG",
    "website": "https://fischbacher.de",
    "summary": "Mengenstaffeln aus einer zentralen Preisliste global in "
               "allen Angeboten und Aufträgen anwenden",
    "description": """
Global Quantity Discounts (Mengenstaffeln)
==========================================

Preisfindung in Angeboten und Aufträgen:

1. Ein Festpreis aus einem noch gültigen Angebot des Kunden
   (Modul sale_customer_offer_price) gilt immer.
2. Sonst gewinnt der niedrigste Preis aus

   * der Preisliste des Kunden bzw. Angebots (kundenspezifische Preise
     gelten nur für diesen Kunden),
   * den als "Global berücksichtigen" markierten Preislisten
     ("Default" mit den Staffelpreisen am Produkt, "Mengenstaffeln (EUR)").

3. Nicht rabattfähige Produkte erhalten keine Rabattregeln, nur
   Festpreise oder den Listenpreis.
""",
    "depends": [
        "sale",
    ],
    "data": [
        "views/product_views.xml",
        "views/product_pricelist_views.xml",
    ],
    "post_init_hook": "post_init_hook",
    "installable": True,
    "application": False,
    "auto_install": False,
    "license": "LGPL-3",
}
