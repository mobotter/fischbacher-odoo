{
    'name': 'partner_history',
    'version': '19.0.1.0.0',
    'author': 'Michael Otto',
    'license': 'LGPL-3',
    'depends': ['base', 'sale'],
    'data': [
        'views/res_partner.xml',
        'security/ir.model.access.csv',
    ],
    'external_dependencies': {"python": [], "bin": []},
    'installable': True,
    'auto_install': False,
}
