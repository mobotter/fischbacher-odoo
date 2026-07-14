# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Adds Custom Fields to Contacts',
    'summary': 'Additional contact fields, sales block for partners, and strict product pricelist locks.',
    'description': '''
Adds custom fields to contacts and partners, including tax information,
telefax, supplier customer number, DSP 3 ID, and a sales block flag.

The module extends sales orders and POS so blocked customers cannot be
selected or sold to.

It also adds a strict pricelist lock on products. For locked products,
manual discounts are forbidden and only product-specific fixed-price
pricelist items are accepted.
''',
    'version': '19.0.2.0.0',
    'author': 'Moritz Kern',
    'depends': ['base', 'product', 'sale_management', 'point_of_sale'],
    'data': [
        'views/res_partner_views.xml',
        'views/product_views.xml',
        'views/sale_order_views.xml',
    ],
    'license': 'LGPL-3',
    'installable': True,
    'application': False,
    'auto_install': False,
}
