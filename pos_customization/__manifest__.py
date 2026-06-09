# -*- coding: utf-8 -*-
{
    'name': 'Point of Sale Customizations',
    'version': '19.0.1.0.2',
    'category': 'Sales/Point of Sale',
    'sequence': 40,
    'author': 'Baqar Hussain',
    'summary': 'Button To Open A Drawer, Show internal reference on product card, Double Receipt Print',
    'depends': ['point_of_sale', 'web', 'base'],
    'data': [],
    'assets': {
        'point_of_sale._assets_pos': [
            'pos_customization/static/src/js/pos.js',
            'pos_customization/static/src/js/double_print.js',   # NEU
            'pos_customization/static/src/xml/pos_button.xml',
            'pos_customization/static/src/xml/product_card.xml',
            'pos_customization/static/src/css/pos_custom.css',
        ],
    },
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
