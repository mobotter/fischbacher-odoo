{
    'name': 'Product Location Column',
    'version': '19.0.1.0.0',
    'summary': 'Shows internal stock locations in the product list view.',
    'author': 'Moritz Kern',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'product',
        'stock',
    ],
    'data': [
        'views/product_template_views.xml',
    ],
    'installable': True,
    'application': False,
}
