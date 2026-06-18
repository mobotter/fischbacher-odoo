{
    'name': 'Invoice Address Email for Partner',
    'version': '19.0.1.0.0',
    'author': 'Aneeq Akhtar | Odolution',
    'website': 'https://odolution.com',
    'license': 'LGPL-3',
    'summary': 'Adds invoice and advertising email management to partners.',
    'depends': [
        'base',
        'mail',
    ],
    'data': [
        'security/server_action.xml',
        'views/res_partner_view.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'sequence': 1,
}
