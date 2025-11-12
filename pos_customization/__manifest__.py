# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Point of Sale Custom Button On Action',
    'version': '1.0.1',
    'category': 'Sales/Point of Sale',
    'sequence': 40,
    'author':'Baqar Hussain | Odolution',
    'summary': 'Button To Open A Drawer',
    'depends': ['point_of_sale' ,'web' , 'base'],
    'data': [],
    'installable': True,
    'application': True,
    'assets': {
        'point_of_sale._assets_pos': [
            'pos_customization/static/src/**/',
            
        ],
    },
    'license': 'LGPL-3',
}
