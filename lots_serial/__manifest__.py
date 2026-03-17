{
    'name': 'Lots Serial',
    'version': '19.0.1.0.0',
    'category': 'invoice',
    'sequence': 10,
    'summary': 'serial numbers / lots',
    'description': """
        This module provides a furniture products
    """,
    'depends': ['stock','web'],
    'data': [
        'views/stock_lot.xml',
    ],
    'demo': [],
    'application': True,
    'installable': True,
}
