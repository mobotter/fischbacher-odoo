{
    "name": "Sale Subscription Fischbacher Extension",
    "version": "19.0.1.5.0",
    "summary": "Fischbacher-spezifische Erweiterungen für das Abonnement-Modul: Rechnungsvorlagen, Berichte, UI-Anpassungen und Ausblenden des Mietdatums in Rechnungszeilen.",
    "description": """
Sale Subscription Fischbacher Extension
========================================

Kundenspezifische Anpassungen für das Odoo-Abonnement- und Mietgeschäft.

Funktionen
----------
- **Rechnungszeilen**: Blendet automatisch generierten Abrechnungszeitraum
  (z. B. „4 Woche(n) 08.06.2026 bis 05.07.2026") aus Produktnamen aus.
  Datenbankfelder (deferred_start/end_date) bleiben unverändert.
- **Berichte**: Eigene Berichtsvorlage und -aktionen für Abonnement-Aufträge.
- **Auftragsvorlagen**: Fischbacher-spezifische Felder in Verkaufsvorlagen.
- **Ansichten**: Angepasste Formular- und Listenansichten für Abonnements.
- **Widget**: ``quotation_line_product_field`` mit Debounce-Fix gegen
  Dropdown-Race-Condition.
- **E-Mail-Vorlagen**: Vorlagen für Abonnement-Kommunikation.

Kompatibilität: Odoo 19.0 Enterprise
    """,
    "author": "Johi Chawla & Moritz Kern",
    "website": "https://www.fischbacher.de",
    "category": "Sales/Subscriptions",
    "license": "LGPL-3",
    "depends": [
        "base",
        "sale_management",
        "stock",
        "sale_subscription",
        "mail",
    ],
    "assets": {
        "web.assets_backend": [
            "ol_sale_subscription_extensions/static/src/js/quotation_line_description_field.js",
            "ol_sale_subscription_extensions/static/src/xml/quotation_line_product_field.xml",
        ],
    },
    "data": [
        "security/ir.model.access.csv",
        "reports/report_action.xml",
        "reports/sale_subscription_report.xml",
        "data/mail_template_data.xml",
        "views/sale_subscription_view.xml",
        "views/sale_order_template_view.xml",
        "views/sale_recurring_plan_view.xml",
    ],
    "installable": True,
    "application": False,
    "auto_install": False,
    "sequence": -1,
}
