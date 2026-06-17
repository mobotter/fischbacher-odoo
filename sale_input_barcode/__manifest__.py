{
    'name': 'Sale Input Barcode',
    'version': '19.0.5.0.0',
    'summary': 'Auto-create the next sale order line after product selection in sales order lines',
    'category': 'Sales/Sales',
    'license': 'AGPL-3',
    'author': 'Moritz Kern',
    'depends': ['sale_management', 'product', 'web'],
    'data': [
        'security/ir.model.access.csv',
        'views/sale_order_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'sale_input_barcode/static/src/js/sale_order_line_autonext.js',
        ],
    },
    'installable': True,
    'application': False,
}
