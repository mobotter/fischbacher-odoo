# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Adds Custom Fields to Contacts',
    'summary': 'Additional contact fields and sales block for partners.',
    'description': '''
Adds custom fields to contacts and partners, including tax information,
telefax, supplier customer number, DSP 3 ID, and a sales block flag.

The module extends sales orders and POS so blocked customers cannot be
selected or sold to.
''',
    'version': '19.0.1.0.0',
    'author': 'Moritz Kern',
    'depends': ['base', 'sale', 'point_of_sale'],
    'data': [
        'views/res_partner_views.xml',
    ],
    'license': 'LGPL-3',
    'installable': True,
    'application': False,
    'auto_install': False,
}
