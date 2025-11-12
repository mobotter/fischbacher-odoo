# -*- coding: utf-8 -*-
{
    'name': 'Product Report',
    'version': '18.1',
    'author': 'Ali Khan | Odolution',
    'website': 'https://odolution.com',
    'depends': [
        'base',
        'stock',
        'web',
        'product'
    ],
    'license' : 'LGPL-3',
    'data': [
        'report/action_product_barcode_report.xml',
        'report/report_product_barcode.xml',
    ],

    'installable': True,
    'application': True,
    'auto_install': False,
    'sequence' : 1,
}

