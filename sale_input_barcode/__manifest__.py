{
    'name': 'Sale Input Barcode',
    'version': '19.0.3.0.0',
    'summary': 'Create a new sale order line for each barcode scan',
    'category': 'Sales/Sales',
    'license': 'AGPL-3',
    'author': 'Moritz Kern',
    'depends': ['sale_management', 'product'],
    'data': [
        'security/ir.model.access.csv',
        'views/sale_order_views.xml',
    ],
    'installable': True,
    'application': False,
}
