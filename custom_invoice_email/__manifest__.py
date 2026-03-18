{
    'name': 'Invoice Address Email for Partner',
    'version': '18.1',
    'author': 'Aneeq Akhtar | Odolution',
    'license': 'LGPL-3'
    'summary': 'in this module we have 3 task 51018,50975,50960',
    'website': 'https://odolution.com',
    'depends': [
        'base','mail'
    ],
    'license' : 'LGPL-3',
    'data': [
        'security/server_action.xml',
        'views/res_partner_view.xml',
    ],

    'installable': True,
    'application': True,
    'auto_install': False,
    'sequence' : 1,
}

