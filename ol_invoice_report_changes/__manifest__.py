# Author: Moritz Kern
# Company: Fischbacher GmbH + Co. KG

{
    "name": "Invoice Report Change",
    "version": "19.0.1.1.0",
    "depends": [
        "base",
        "account",
        "l10n_din5008",
        "sale",
        "mail",
        "sale_pdf_quote_builder",
        "sale_subscription",
        "sale_renting",
        "repair",
        "contact_custom_fields",
        "stock_dropshipping",
        "repair",
    ],
    "author": "Moritz Kern, Baqar Hussain and Johi Chawla",
    "license": "LGPL-3",
    "category": "Account",
    "summary": (
        "Angepasste Rechnungs- und Verkaufsberichte "
        "mit Mietvertragsverknüpfung"
    ),
    "description": """
Invoice Report Changes
======================

Firma: Fischbacher GmbH + Co. KG

Dieses Modul passt das Rechnungs-Layout an und ergänzt folgende Funktionen:

- Benutzerdefiniertes Rechnungs-Layout
- Streckengeschäft-Indikator auf Rechnungspositionen
- Angepasste Berichte für Verkaufsangebote und Auftragsbestätigungen
- Zusätzliche Auftrags- und Kundenreferenzen
- Individueller Einleitungstext und Lieferzeit
- Auswahl eines zugehörigen Mietpark-Vertrags oder GEDA-Abos
- Automatische Ermittlung der Mietvertragsnummer am Verkaufsauftrag

Mietvertragsverknüpfung:
- Das bestehende Feld lease_agreement_no bleibt erhalten.
- Das neue Many2one-Feld steht direkt hinter lease_agreement_no.
- Zusätzliche Aufträge können einem Mietpark-Vertrag oder Abo zugeordnet werden.
- Ohne übergeordneten Vertrag verwenden Mietpark-Verträge und Abos
  ihre eigene Angebots- oder Auftragsnummer als Mietvertragsnummer.
- Die eigenen Nummern zusätzlicher Verkaufsaufträge bleiben unverändert.

Streckengeschäft-Erkennung:
- Zeigt "(Streckengeschäft)" nach der Produktbeschreibung
  bei Dropshipping-Positionen.
- Erfordert eine aktivierte Dropshipping-Route im Produkt.
""",
    "data": [
        # Fundament für alle PDF-Berichte
        "reports/paperformat.xml",
        "reports/external_layout.xml",

        # QWeb-Report-Templates
        "reports/account_move_report.xml",
        "reports/pro_forma_invoice_quotation_report.xml",
        "reports/sale_order_report.xml",
        "reports/sale_order_confirmation_report.xml",

        # ir.actions.report:
        # Erst nachdem Templates und Paperformat existieren
        "views/report_action.xml",

        # Backend-Formular-, Listen- und Vorschau-Views
        "views/res_partner_view.xml",
        "views/sale_order.xml",
        "views/repair_order.xml",
        "views/sale_order_preview.xml",

        # Sonstige Datensätze
        "data/mail_template_data.xml",
    ],
    "installable": True,
    "application": False,
    "sequence": -10,
    "auto_install": False,
}
