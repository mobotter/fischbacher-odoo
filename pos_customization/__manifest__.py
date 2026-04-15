# -*- coding: utf-8 -*-
{
    'name': 'Point of Sale Customizations',
    'version': '18.0.1.0.0',
    'category': 'Point of Sale',
    'sequence': 40,
    'author': 'Baqar Hussain',
    'summary': 'POS drawer button and internal reference on product cards',
    'depends': ['point_of_sale'],
    'data': [],
    'assets': {
        'point_of_sale._assets_pos': [
            'pos_customization/static/src/js/**/*.js',
            'pos_customization/static/src/xml/**/*.xml',
            'pos_customization/static/src/scss/**/*.scss',
        ],
    },
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
