# -*- coding: utf-8 -*-
{
    'name': 'Purchase Order Report Changes',
    'version': '19.0.1.0.0',
    'category': 'Purchase',
    'summary': 'Custom PDF layout for purchase orders',
    'description': """
Purchase Order Report Changes
=============================

Dieses Modul passt den PDF-Bericht für Einkaufsbestellungen an.

Funktionen:
- Einheitliches Layout passend zum benutzerdefinierten Rechnungsbericht
- DIN-5008-orientiertes Brief-/Adressfenster
- Lieferantenanschrift im Anschriftenfenster
- Informationsblock mit Bestell-, Lieferanten- und Kontaktdaten
- Einheitliche Positions- und Summendarstellung
- Verwendung des Papierformats und des externen Layouts aus
  ol_invoice_report_changes
""",
    'author': 'Moritz Kern',
    'license': 'LGPL-3',
    'depends': [
        'purchase',
        'ol_invoice_report_changes',
    ],
    'data': [
        'reports/purchase_quotation_report.xml',
        'reports/purchase_order_report.xml',
        'views/report_action.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'sequence': -9,
}
