{
    'name': 'Invoice Report Change',
    'version': '19.0.1.0.0',
    'depends': ['base','account','l10n_din5008','sale','mail','sale_pdf_quote_builder'],
    'author': 'Baqar Hussain and Johi Chawla',
    'license': 'LGPL-3'
    'category': 'Account',
    'summary': 'Changes on the invoice report',
    'data': [
        'views/paperformat.xml',
        'views/report_action.xml',
        'views/external_layout.xml',
        'views/account_move_report.xml',
        'views/pro_forma_invoice_quotation_report.xml',
        'views/sale_order_report.xml',
        'views/sale_order_confirmation_report.xml',
        'views/sale_order.xml',
        'views/sale_order_preview.xml',
        'views/res_partner_view.xml',
        'data/mail_template_data.xml'
    ],
    'installable': True,
    'application': False,
    'sequence' : -10
}
