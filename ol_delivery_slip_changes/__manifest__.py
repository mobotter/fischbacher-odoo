{
    'name': 'delivery Slip Report Changes',
    'version': '18.0',
    'depends': ['base','stock','l10n_din5008','ol_invoice_report_changes','sale','product'],
    'author': 'Johi Chawla',
    'category': 'stock',
    'summary': 'Changes on the delivery slip  report',
    'data': [
        # 'views/report_action.xml',
        'views/sale_order.xml',       # jc work
        'views/stock_picking.xml',       # jc work
        'views/delivery_slip_new_report.xml',       # jc work
        'views/picking_operation_new_report.xml', #jc work

    ],
    'installable': True,
    'application': False,
    'sequence' : -2,
}
