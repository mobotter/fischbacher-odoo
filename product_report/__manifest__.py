# -*- coding: utf-8 -*-
{
    'name': 'Product Report',
    'version': '19.0.1.0.0',
    'author': 'Ali Khan | Odolution',
    'license': 'LGPL-3'
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
        'report/zpl_product_barcode_report.xml',
    ],

    'installable': True,
    'application': True,
    'auto_install': False,
    'sequence' : 1,
}

