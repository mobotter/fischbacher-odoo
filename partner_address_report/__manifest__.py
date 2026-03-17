{
    'name': 'Partner Address Report',
    'version': '19.0.1.0.0',
    'depends': ['base'],
    'author': 'Your Name',
    'category': 'Contacts',
    'summary': 'Custom printable report for res.partner',
    'data': [
        'report/partner_report_template.xml',
        'report/partner_report_action.xml',
        'report/zpl_partner_report_template.xml',
    ],
    'installable': True,
    'application': False,
}
