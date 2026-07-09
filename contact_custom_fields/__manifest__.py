# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Adds Custom Fields to Contacts',
    'version': '19.0.1.0.0',
    'author': 'Odolution & Moritz Kern',
    'depends': ['base', 'sale'],
    'data': [
        'views/res_partner_views.xml',
        'views/sale_order_views.xml',
    ],
    'external_dependencies': {
    },
    'license': 'LGPL-3',
    'installable': True,
    'application': False,
    'auto_install': False,
}
