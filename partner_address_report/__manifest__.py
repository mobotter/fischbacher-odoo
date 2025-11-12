{
    'name': 'Partner Address Report',
    'version': '18.0',
    'depends': ['base'],
    'author': 'Your Name',
    'category': 'Contacts',
    'summary': 'Custom printable report for res.partner',
    'data': [
        'report/partner_report_template.xml',
        'report/partner_report_action.xml',
    ],
    'installable': True,
    'application': False,
}
