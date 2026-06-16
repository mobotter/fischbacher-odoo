{
    "name": "Sale Subscription Fischbacher Extension",
    "version": "19.0.1.4.0",
    "summary": "Fischbacher-spezifische Erweiterungen für das Abonnement-Modul: Rechnungsvorlagen, Berichte, UI-Anpassungen und Ausblenden des Mietdatums in Rechnungszeilen.",
    "description": """
Sale Subscription Fischbacher Extension
========================================

Dieses Modul enthält alle kundenspezifischen Anpassungen von Fischbacher
für das Odoo-Abonnement- und Mietgeschäft.

Funktionen
----------

**Rechnungsdarstellung**
- Blendet den automatisch generierten Abrechnungszeitraum (z. B. „4 Woche(n)
  08.06.2026 bis 05.07.2026") unter jeder Rechnungszeile aus.
  Technisch: Override von _prepare_invoice_line auf sale.order.line.
  Odoo hängt den Zeitraum per \\n an den Produktnamen an (Zeile ~432 in
  enterprise/sale_subscription/models/sale_order_line.py).
  Dieser Teil wird vor dem Speichern in account.move.line entfernt.
  Die Felder deferred_start_date / deferred_end_date bleiben in der
  Datenbank erhalten.

**Abonnement-Berichte**
- Eigene Berichtsvorlage für Abonnement-Aufträge (sale_subscription_report.xml).
- Angepasste Berichtsaktionen (report_action.xml).

**Auftragsvorlagen**
- Erweiterung der Verkaufsauftragsvorlagen um Fischbacher-spezifische Felder
  (sale_order_template_view.xml).

**Abonnement-Ansichten**
- Angepasste Formular- und Listenansichten für Abonnements
  (sale_subscription_view.xml).

**Frontend-Komponente**
- Benutzerdefiniertes Widget ``quotation_line_product_field`` für die
  Produktauswahl in Angebotspositionen (JS + QWeb-Template).
- Fix: Debounce auf record.update() verhindert Dropdown-Race-Condition
  (TypeError: Cannot read properties of undefined (reading 'dataset')).

**E-Mail-Vorlagen**
- Vordefinierte Mail-Templates für Abonnement-bezogene Kommunikation
  (mail_template_data.xml).

Technische Details
------------------
- Kompatibel mit: Odoo 19.0 Enterprise
- Abhängigkeiten: base, sale_management, stock, sale_subscription, mail
- Lizenz: LGPL-3
- Kein Datenverlust: Alle Datenbankfelder bleiben unverändert erhalten;
  Änderungen betreffen ausschließlich die Darstellungsebene (Views/Templates).

Entwickler
----------
Johi Chawla & Moritz Kern
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
        "mail"
    ],
    'assets': {
        'web.assets_backend': [
            'ol_sale_subscription_extensions/static/src/js/quotation_line_description_field.js',
            'ol_sale_subscription_extensions/static/src/xml/quotation_line_product_field.xml',
        ],
    },
    "data": [
        "security/ir.model.access.csv",
        "reports/report_action.xml",
        "reports/sale_subscription_report.xml",
        "data/mail_template_data.xml",
        "views/sale_subscription_view.xml",
        'views/sale_order_template_view.xml',
        "views/account_invoice_report_override.xml",
    ],
    "installable": True,
    "application": False,
    "auto_install": False,
    "sequence": -1,
}
