# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': 'Adds Dymo Barcode Report',
    'version': '19.0.1.0.0',
    'category': 'Inventory/Delivery',
    'summary': 'Fügt spezielle Dymo- und ZPL-Etiketten für Produkte und Lagerorte hinzu',
    'description': """
        Dieses Modul erweitert die Standard-Etikettendruckfunktion um:
        - Dymo Label Formate (mit/ohne Preis, kleine Etiketten)
        - ZPL Formate für Industriedrucker (Zebra etc.)
        - Spezifische Barcode-Layouts für Lagerorte (stock.location)
    """,
    'author': 'Odolution',
    'depends': [
        'product', 
        'sale', 
        'stock'
    ],
    'data': [
        'report/dymo_barcode_report.xml',
        'report/report_simple_label_dymo.xml',
        'report/report_stock_label_dymo.xml',
        'report/zpl_product_report.xml',
        'views/product_label_wizard_action.xml',
        'views/product_form_print_label_button.xml',
        'actions/product_label_layout.xml',
    ],
    'external_dependencies': {},
    'installable': True,
    'application': False,
    'license': 'LGPL-3'
}
