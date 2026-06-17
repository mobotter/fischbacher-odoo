{
    'name': 'Sale Input Barcode 19',
    'version': '19.0.1.0.0',
    'summary': 'Add sale order lines by scanning product barcodes in sales orders',
    'category': 'Sales/Sales',
    'author': 'Moritz Kern',
    'license': 'AGPL-3',
    'author': 'OpenAI',
    'depends': ['sale_management', 'product', 'web'],
    'data': [
        'security/ir.model.access.csv',
        'views/sale_order_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'sale_input_barcode_19/static/src/js/sale_barcode_button.js',
            'sale_input_barcode_19/static/src/xml/sale_barcode_button.xml',
        ],
    },
    'installable': True,
    'application': False,
}
