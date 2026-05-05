# -*- coding: utf-8 -*-
{
    'name': 'Point of Sale Customizations',
    'version': '19.0.1.0.1',
    'category': 'Sales/Point of Sale',
    'sequence': 40,
    'author':'Baqar Hussain',
    'summary': 'Button To Open A Drawer, Show internal refernce on product card',
    'depends': ['point_of_sale', 'web', 'base'],
    'data': [],
    'assets': {
        'point_of_sale._assets_pos': [
            'pos_customization/static/src/js/**/*.js',
            'pos_customization/static/src/xml/**/*.xml',
            'pos_customization/static/src/scss/**/*.scss',
        ],
    },
    'installable': True,
    'application': True,
    'assets': {
        'point_of_sale._assets_pos': [
            # WICHTIG: Gib hier die genauen Pfade an, um Ladefehler zu vermeiden
            'pos_customization/static/src/js/pos.js',
            'pos_customization/static/src/xml/pos_button.xml',
            'pos_customization/static/src/xml/product_card.xml',
            'pos_customization/static/src/css/pos_custom.css',
        ],
    },
    'license': 'LGPL-3',
}
