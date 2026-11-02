# Copyright (c) 2026 Moritz Kern, Fischbacher GmbH + Co. KG
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.html)
{
    "name": "Sale Customer Offer Price",
    "version": "19.0.1.1.0",
    "category": "Sales",
    "author": "Moritz Kern, Fischbacher GmbH + Co. KG",
    "website": "https://fischbacher.de",
    "summary": "Günstigere Preise aus laufenden Kundenangeboten finden "
               "und als Festpreis übernehmen",
    "description": """
Sale Customer Offer Price
=========================

Prüft in offenen Angeboten (Status Entwurf oder Gesendet), ob für denselben
kommerziellen Kunden ein anderes gültiges, laufendes Angebot mit demselben
Produkt, derselben Mengeneinheit, Gesellschaft und Währung einen günstigeren
effektiven Einzelpreis enthält.

Ein Assistent zeigt die günstigste Quellposition an und übernimmt deren
effektiven Preis (inklusive Positionsrabatt) auf Wunsch als Festpreis:

* Der Rabatt der Zielposition wird auf 0,00 % gesetzt.
* Ein Festpreis ist nicht rabattierbar.
* Mengenänderungen und "Preise aktualisieren" berechnen den Festpreis nicht
  über die Preisliste neu.
* Eine manuelle Preisänderung wird als manueller Festpreis geführt.

Bestätigte Aufträge, stornierte Angebote, Rechnungen und POS-Vorgänge werden
nicht beeinflusst.
""",
    "depends": [
        "sale",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/customer_offer_price_wizard_views.xml",
        "views/sale_order_views.xml",
    ],
    "license": "LGPL-3",
    "installable": True,
    "application": False,
}
