# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': 'Adds Dymo Barcode Report',
    'depends': ['sale'],
    'data': [
        'report/dymo_barcode_report.xml',
        'report/report_simple_label_dymo.xml',
        'report/report_stock_label_dymo.xml',
        'report/zpl_product_report.xml'
    ],
    'external_dependencies': {},
    'license': 'LGPL-3',
}