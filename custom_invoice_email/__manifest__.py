{
    'name': 'Invoice Address Email for Partner',
    'version': '19.0.1.0.0',
    'author': 'Aneeq Akhtar | Odolution',
    'website': 'https://odolution.com',
    'license': 'LGPL-3',
    'category': 'Contacts',
    'summary': 'Adds invoice and advertising email management to partners.',
    'description': """
This module extends partners with:
- invoice email handling
- advertising email handling
- blacklist synchronization
- partner email update server action
""",
    'depends': [
        'base',
        'mail',
    ],
    'data': [
        'security/server_action.xml',
        'views/res_partner_view.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'sequence': 1,
}
