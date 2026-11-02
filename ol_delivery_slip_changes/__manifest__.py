{
    'name': 'Kombinierter Lieferschein (Gesamt)',
    'version': '19.0.1.1.4',
    'depends': [
        'base',
        'stock',
        'sale',
        'product',
        'l10n_din5008',
        'ol_invoice_report_changes',
        'ol_extension',
        'stock_dropshipping',
    ],
    'author': 'Johi Chawla & Moritz Kern',
    'license': 'LGPL-3',
    'category': 'Inventory/Delivery',
    'summary': (
        'Lieferschein, Kommissionierschein, '
        'Kombinierter Lieferschein über alle Positionen '
        '(Produkte, Dienstleistungen, Streckengeschäfte)'
    ),
    'data': [
        'views/sale_order.xml',
        'views/stock_picking.xml',
        'views/rental_equipment_issue_slip_report_template.xml',
    
        # Kombinierter Lieferschein:
        # erst QWeb-Vorlage, danach die Report-Action, dann der Smartbutton
        'reports/sale_combined_delivery_template_new.xml',
        'views/sale_combined_delivery_report.xml',
        'views/sale_order_views.xml',
    
        'reports/delivery_slip_new_report.xml',
        'reports/picking_operation_new_report.xml',
        'reports/rental_equipment_issue_slip_report.xml',
    ],
    'installable': True,
    'application': False,
    'sequence': 110,
}
