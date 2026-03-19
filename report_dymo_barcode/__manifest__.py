# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': 'Adds Dymo Barcode Report',
    'version': '19.0.1.0.0',
    'author': 'Odolution',
    'depends': ['sale'],
    'data': [
        'report/dymo_barcode_report.xml',
        'report/report_simple_label_dymo.xml',
        'report/report_stock_label_dymo.xml',
        'report/zpl_product_report.xml'
    ],
    'external_dependencies': {},
    'license': 'LGPL-3'
}
